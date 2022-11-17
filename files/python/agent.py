import datetime
import hashlib
import logging
import os
import re
import sys
import time
import requests as requests
from urllib3.exceptions import InsecureRequestWarning
from files.python.constants import HOURS_IN_DAY, TYPE_LIST_HELP, DATE_TIME_FORMAT, DATE_FORMAT, IP_TYPES, HASH_TYPES, SQL_TO_LIST_ALL_IOCS, SQL_TO_GET_LAST_SYNC, \
    SQL_TO_ADD_LAST_SYNC, SQL_TO_GET_IOC_BY_MD5, SQL_TO_ADD_IOC, SQL_TO_UPDATE_LAST_SYNC, SQL_TO_ADD_IOC_EXCEPTION, \
    SQL_TO_DELETE_IOC_BEFORE_EXCEPTION, SQL_TO_GET_IOC_BEFORE_DELETE
from files.python.global_functions import get_type_and_feed_lists, is_ipv4, is_ipv6, maybe_a_file, is_dual_value, \
    calc_lived_days, is_exception, progress_logging, check_run_status
from files.python.reflect_db_to_siem import reflect_db_to_siem
from files.python.reflect_siem_to_db import mark_as_false_positive
from files.python.update_lived_days import update_lived_days
from files.python.sqlite_functions import execution_start_register, sqlite_command, execution_stop_register, \
    connection_error_register


requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


def agent(all_settings, events_count_by_type):
    """ Function to adjust remaining days of IOCs and get IOCs from MISP > Save on local database > Sync with SIEM. """

    check_run_status(all_settings)

    # Initialize variables
    mode = 'AGENT'
    final_status = ''
    success_count = 0
    database_updates = 0

    # Register in local database when the function starts
    execution_id = execution_start_register(all_settings, mode)

    try:
        
        # Adjust lived days of each IOCs in local database
        update_lived_days(all_settings, mode)
    
        # Get from local database the amount of IOCs
        total_of_iocs_in_db = sqlite_command(all_settings, SQL_TO_LIST_ALL_IOCS)[1]
        total_of_iocs_in_db = len(total_of_iocs_in_db)
        message = 'mode="{}" details="Total IOCs in local database" value="{}"'.format(mode, total_of_iocs_in_db)
        logging.info(message)

        # Get the lists of types and custom feeds
        type_list, custom_feed = get_type_and_feed_lists(all_settings, execution_id)
        type_list_amount = len(type_list)
        message = 'mode="{}" details="Total type list" value="{}"'.format(mode, type_list_amount)
        logging.info(message)

        # Reflect the IOCs in db to SIEM
        logging.debug("Starting: reflect_db_to_siem")
        reflect_db_to_siem(all_settings, execution_id)
        logging.debug("Ending: reflect_db_to_siem")
        logging.debug("Starting: mark_as_false_positive")
        mark_as_false_positive(all_settings, execution_id)
        logging.debug("Ending: mark_as_false_positive")

        # Check if the type_list no has at least one IOC type configured
        if type_list_amount == 0:
            logging.warning(TYPE_LIST_HELP)
            execution_stop_register(all_settings, execution_id, TYPE_LIST_HELP)
            quit()

        # Run for each IOC type configured
        for ioc_type_settings in type_list:

            message = 'details="Starting loop for" value="{} {}"'.format(ioc_type_settings, type_list[ioc_type_settings])
            logging.info(message)

            # Settings for this type
            type_ttl = type_list[ioc_type_settings]['ttl']

            # Body used to get created attributes in timestamp range
            body_by_type = all_settings['MISP_SETTINGS']['MISP_BODY_BY_TYPE']
            body_by_type['type']['AND'].clear()
            body_by_type['type']['AND'].append(ioc_type_settings)

            # Body used to get sightings
            body_sightings = all_settings['MISP_SETTINGS']['MISP_BODY_SIGHTINGS']

            # Body used to get last updates in MISP
            body_last_updates = all_settings['MISP_SETTINGS']['MISP_BODY_LAST_UPDATES']
            body_last_sightings = all_settings['MISP_SETTINGS']['MISP_BODY_SIGHTINGS']

            # Get this execution date and time
            now = datetime.datetime.now()
            timestamp_last_updates = now - datetime.timedelta(hours=all_settings['BROKER_SETTINGS']['UPDATE_LOOKBACK'])
            now = now + datetime.timedelta(days=1)

            # Logging string complementary
            step_type = 'mode="{}" type="{}"'.format(mode, ioc_type_settings)

            # Try to get local database if this IOC type has already been synced before else then create an input in db
            last_sync = sqlite_command(all_settings, SQL_TO_GET_LAST_SYNC, (ioc_type_settings,))

            if last_sync[1]:
                last_sync_date = last_sync[1][0][0]
                last_sync_date = datetime.datetime.strptime(last_sync_date, DATE_TIME_FORMAT)
            else:
                message = '{} details="Creating this type in local database" value="{}"'.format(step_type,
                                                                                                ioc_type_settings)
                logging.info(message)

                last_sync_date = '{} 00:00:00'.format(all_settings['BROKER_SETTINGS']['START_DATE'])

                sqlite_command(all_settings, SQL_TO_ADD_LAST_SYNC, (ioc_type_settings, last_sync_date))

                last_sync_date = datetime.datetime.strptime(last_sync_date, DATE_TIME_FORMAT)

            # Try to get the time to live for this IOC, if is not configured then use the default in settings
            try:
                days = int(type_ttl)

                if days == 0:
                    days = (now - datetime.datetime.strptime(all_settings['BROKER_SETTINGS']['START_DATE'], DATE_FORMAT)).days

            except Exception as e:
                message = '{} details="Using the default TTL for" value="{}" status={}'.format(step_type, e,
                                                                                               ioc_type_settings)
                logging.warning(message)
                days = int(all_settings['BROKER_SETTINGS']['DEFAULT_TTL'])

            total_hours = days * HOURS_IN_DAY

            earliest = now - datetime.timedelta(hours=total_hours)
            earliest = earliest.replace(hour=0, minute=0, second=0)

            if int(earliest.timestamp()) < int(last_sync_date.timestamp()):
                earliest = last_sync_date.replace(hour=0, minute=0, second=0)
                total_hours = (now - earliest).days * HOURS_IN_DAY
                if total_hours <= all_settings['BROKER_SETTINGS']['RANGE_TIME']:
                    total_hours = all_settings['BROKER_SETTINGS']['RANGE_TIME']

            message = '{} earliest="{}" latest="{}" ' \
                      'details="TTL in days for this type" ' \
                      'value="{}" total_hours="{}" type_ttl="{}"'.format(step_type, earliest.strftime(DATE_TIME_FORMAT),
                                                                         now.strftime(DATE_TIME_FORMAT), days, total_hours, type_ttl)

            logging.info(message)

            hour_count = 0
            while hour_count <= total_hours:
                hour_count += all_settings['BROKER_SETTINGS']['RANGE_TIME']

                events_on_misp = {}

                latest = earliest + datetime.timedelta(hours=(all_settings['BROKER_SETTINGS']['RANGE_TIME'] - 1))
                latest = latest.replace(hour=23, minute=59, second=59)

                iocs_from_misp = []
                body_by_type['from'] = earliest.strftime(DATE_TIME_FORMAT)
                body_by_type['to'] = latest.strftime(DATE_TIME_FORMAT)

                timestamp_last_updates = datetime.datetime.now() - datetime.timedelta(hours=all_settings['BROKER_SETTINGS']['UPDATE_LOOKBACK'])
                body_last_updates['timestamp'] = timestamp_last_updates.strftime(DATE_TIME_FORMAT)
                body_last_sightings['last'] = str(int(timestamp_last_updates.timestamp()))

                step_timestamp = '{} earliest="{}" latest="{}" hour_count="{}" total_hours="{}"'.format(step_type, body_by_type['from'],
                                                                                                        body_by_type['to'], hour_count, total_hours)

                logging.debug('body_by_type: {}'.format(body_by_type))
                logging.debug('body_sightings: {}'.format(body_sightings))
                logging.debug('body_last_updates: {}'.format(body_last_updates))
                logging.debug('body_last_sightings: {}'.format(body_last_sightings))

                misp_connection_status = False
                while not misp_connection_status:
                    try:
                        iocs_from_misp.clear()

                        try:
                            etotal = events_count_by_type[ioc_type_settings]

                        except Exception:
                            etotal = 0

                        message = '{} details="Trying to connect to MISP server"'.format(step_timestamp)
                        logging.info(message)

                        message = '{} details="Starting requests" URL="{}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['MISP_API_URL'])
                        logging.info(message)
                        response = requests.post(all_settings['MISP_SETTINGS']['MISP_API_URL'], headers=all_settings['MISP_SETTINGS']['MISP_HEADERS'], json=body_by_type, verify=all_settings['MISP_SETTINGS']['MISP_VERIFY_SSL'])
                        message = '{} details="Requests done" status_code="{}"'.format(step_timestamp, response.status_code)
                        logging.info(message)
                        query_json = response.json()
                        try:
                            ttotal = len(query_json['response']['Attribute'])
                        except Exception:
                            ttotal = 0

                        message = '{} details="Last daily update count was {}, this update has {}'.format(step_timestamp, etotal, ttotal)

                        if etotal != ttotal:
                            iocs_from_misp = query_json['response']['Attribute']
                            message = '{}, getting daily update"'.format(message)
                        else:
                            message = '{}, skipping daily update"'.format(message)

                        logging.info(message)

                        message = '{} details="Starting requests" URL="{}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['MISP_API_URL'])
                        logging.info(message)
                        response = requests.post(all_settings['MISP_SETTINGS']['MISP_API_URL'], headers=all_settings['MISP_SETTINGS']['MISP_HEADERS'], json=body_last_updates,
                                                 verify=all_settings['MISP_SETTINGS']['MISP_VERIFY_SSL'])
                        message = '{} details="Requests done" status_code="{}"'.format(step_timestamp, response.status_code)
                        logging.info(message)
                        query_json = response.json()
                        try:
                            for item in query_json['response']['Attribute']:
                                iocs_from_misp.append(item)
                        except Exception as e:
                            details = '{} details="Cannot get last updated attributes" ' \
                                      'value="{} {}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['MISP_API_URL'], e)
                            logging.error(details)

                        message = '{} details="Starting requests" URL="{}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['SIGHTINGS_RECENT_URL'])
                        logging.info(message)
                        response = requests.post(all_settings['MISP_SETTINGS']['SIGHTINGS_RECENT_URL'], headers=all_settings['MISP_SETTINGS']['MISP_HEADERS'], json=body_last_sightings,
                                                 verify=all_settings['MISP_SETTINGS']['MISP_VERIFY_SSL'])
                        message = '{} details="Requests done" status_code="{}"'.format(step_timestamp, response.status_code)
                        logging.info(message)
                        query_json = response.json()

                        value_list = []
                        attributes_sightings_json = {}

                        try:
                            for item in query_json['response']:
                                value_list.append(str(str(item['Sighting']['value']).replace('%', '\%')))
                        except Exception as e:
                            details = '{} details="Cannot get last updated sightings" ' \
                                      'value="{} {} {}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['MISP_API_URL'], e, query_json)
                            logging.error(details)

                        if value_list:

                            message = '{} details="New {} sightings to sync"'.format(step_timestamp, len(value_list))
                            logging.info(message)

                            split_data_list = []
                            count = 0
                            max_amount = 100

                            for index in range(0, len(value_list), max_amount):
                                split_data_list.append(value_list[index: index + max_amount])

                            for splitter_list in split_data_list:

                                count += 1

                                message = '{} details="Getting sightings values" list="{}/{}"'.format(step_timestamp, count, len(split_data_list))
                                logging.info(message)

                                if len(splitter_list) > 0:
                                    attributes_sightings_json = {'returnFormat': 'json', 'value': {'OR': splitter_list}}
                                    logging.debug(attributes_sightings_json)

                                    try:
                                        message = '{} details="Starting requests" URL="{}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['MISP_API_URL'])
                                        logging.info(message)
                                        response = requests.post(all_settings['MISP_SETTINGS']['MISP_API_URL'], headers=all_settings['MISP_SETTINGS']['MISP_HEADERS'], json=attributes_sightings_json,
                                                                verify=all_settings['MISP_SETTINGS']['MISP_VERIFY_SSL'], timeout=120)
                                        message = '{} details="Requests done" status_code="{}"'.format(step_timestamp, response.status_code)
                                        logging.info(message)
                                        query_json = response.json()

                                        for item in query_json['response']['Attribute']:
                                            iocs_from_misp.append(item)
                                    except Exception as e:
                                        message = '{} details="Timeout" status="{}"'.format(step_timestamp, e)
                                        logging.warning(message)

                        misp_connection_status = True
                        events_count_by_type[ioc_type_settings] = ttotal
                    except Exception as e:
                        details = '{} details="Cannot connect to MISP server" ' \
                                  'value="{} {}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['MISP_API_URL'], e)
                        connection_error_register(all_settings, 'MISP', details)
                        time.sleep(all_settings['BROKER_SETTINGS']['WAIT_TIME'])

                    check_run_status(all_settings, execution_id)

                earliest = earliest + datetime.timedelta(hours=all_settings['BROKER_SETTINGS']['RANGE_TIME'])

                ioc_count = 0
                ioc_update = 0
                max_amount = 2000
                split_data_list = []

                for index in range(0, len(iocs_from_misp), max_amount):
                    split_data_list.append(iocs_from_misp[index: index + max_amount])

                for iocs in split_data_list:

                    try:

                        timestamp_last_updates = datetime.datetime.now() - datetime.timedelta(hours=all_settings['BROKER_SETTINGS']['UPDATE_LOOKBACK'])
                        body_last_updates['timestamp'] = timestamp_last_updates.strftime(DATE_TIME_FORMAT)
                        body_last_sightings['last'] = str(int(timestamp_last_updates.timestamp()))

                        logging.debug('body_last_updates: {}'.format(body_last_updates))

                        message = '{} details="Starting requests" URL="{}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['SIGHTINGS_RECENT_URL'])
                        logging.info(message)
                        response = requests.post(all_settings['MISP_SETTINGS']['SIGHTINGS_RECENT_URL'], headers=all_settings['MISP_SETTINGS']['MISP_HEADERS'], json=body_last_sightings,
                                                 verify=all_settings['MISP_SETTINGS']['MISP_VERIFY_SSL'])
                        message = '{} details="Requests done" status_code="{}"'.format(step_timestamp, response.status_code)
                        logging.info(message)
                        query_json = response.json()

                        value_list = []
                        attributes_sightings_json = {}

                        try:
                            for item in query_json['response']:
                                value_list.append(str(str(item['Sighting']['value']).replace('%', '\%')))
                        except Exception as e:
                            details = '{} details="Cannot get last updated sightings" ' \
                                      'value="{} {} {}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['MISP_API_URL'], e, query_json)
                            logging.error(details)

                        if value_list:

                            message = '{} details="New {} sightings to sync"'.format(step_timestamp, len(value_list))
                            logging.info(message)

                            split_data_list = []
                            count = 0
                            max_amount = 100

                            for index in range(0, len(value_list), max_amount):
                                split_data_list.append(value_list[index: index + max_amount])

                            for splitter_list in split_data_list:

                                count += 1

                                message = '{} details="Getting sightings values" list="{}/{}"'.format(step_timestamp, count, len(split_data_list))
                                logging.info(message)

                                if len(splitter_list) > 0:
                                    attributes_sightings_json = {'returnFormat': 'json', 'value': {'OR': splitter_list}}
                                    logging.debug(attributes_sightings_json)

                                    try:
                                        message = '{} details="Starting requests" URL="{}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['MISP_API_URL'])
                                        logging.info(message)
                                        response = requests.post(all_settings['MISP_SETTINGS']['MISP_API_URL'], headers=all_settings['MISP_SETTINGS']['MISP_HEADERS'], json=attributes_sightings_json,
                                                                verify=all_settings['MISP_SETTINGS']['MISP_VERIFY_SSL'], timeout=120)
                                        message = '{} details="Requests done" status_code="{}"'.format(step_timestamp, response.status_code)
                                        logging.info(message)
                                        query_json = response.json()

                                        for item in query_json['response']['Attribute']:
                                            iocs.append(item)

                                    except Exception as e:
                                        message = '{} details="Timeout" status="{}"'.format(step_timestamp, e)
                                        logging.warning(message)

                    except Exception as e:
                        details = '{} details="Cannot connect to MISP server to get sightings" ' \
                                  'value="{} {}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['MISP_API_URL'], e)
                        logging.warning(details)

                    for ioc in iocs:

                        value = str(ioc['value'])
                        value = re.sub(r'\\+$', '', value)
                        ioc_type = str(ioc['type'])
                        event = str(ioc['event_id'])
                        attribute_timestamp = datetime.datetime.fromtimestamp(int(ioc['timestamp']))
                        attribute_timestamp = attribute_timestamp.strftime(DATE_TIME_FORMAT)

                        misp_connection_status = False
                        while not misp_connection_status:
                            if event not in events_on_misp:
                                try:
                                    message = '{} details="Getting sightings list to event {}" count="{}/{}/{}"'.format(step_timestamp,
                                                                                                                        event,
                                                                                                                        str(ioc_count).zfill(4),
                                                                                                                        str(len(iocs_from_misp)).zfill(4),
                                                                                                                        str(database_updates).zfill(4))
                                    logging.info(message)

                                    message = '{} details="Starting requests" URL="{}"'.format(step_timestamp, '{}{}'.format(all_settings['MISP_SETTINGS']['SIGHTINGS_URL'], event))
                                    logging.info(message)
                                    response = requests.post('{}{}'.format(all_settings['MISP_SETTINGS']['SIGHTINGS_URL'], event), headers=all_settings['MISP_SETTINGS']['MISP_HEADERS'],
                                                             json=body_sightings, verify=all_settings['MISP_SETTINGS']['MISP_VERIFY_SSL'])
                                    message = '{} details="Requests done" status_code="{}"'.format(step_timestamp, response.status_code)
                                    logging.info(message)
                                    query_json = response.json()
                                    events_on_misp[event] = query_json
                                    misp_connection_status = True
                                except Exception as e:
                                    details = '{} details="Cannot connect to MISP server to get attribute sighting" ' \
                                              'value="{} {}"'.format(step_timestamp, all_settings['MISP_SETTINGS']['MISP_API_URL'], e)
                                    connection_error_register(all_settings, 'MISP', details)
                                    time.sleep(all_settings['BROKER_SETTINGS']['WAIT_TIME'])
                            else:
                                misp_connection_status = True

                            check_run_status(all_settings, execution_id)

                        step_type = 'mode="{}" type="{}/{}"'.format(mode, ioc_type_settings, ioc_type)
                        step_timestamp = '{} earliest="{}" latest="{}"'.format(step_type, body_by_type['from'],
                                                                               body_by_type['to'])

                        check_dual_value = is_dual_value(ioc_type_settings, value)

                        if check_dual_value[0] and not check_dual_value[1]:
                            check_dual_value = is_dual_value(ioc_type, value)

                            if check_dual_value[0] and not check_dual_value[1]:
                                message = '{} details="Skipping because is an dual-type but not an dual-value" ' \
                                          'count="{}/{}" value="{}"'.format(step_timestamp,
                                                                            str(ioc_count).zfill(4),
                                                                            str(database_updates).zfill(4),
                                                                            value)
                                logging.info(message)
                                continue

                        tags = []
                        try:
                            for tag in ioc['Tag']:
                                tags.append(tag)
                        except Exception:
                            pass

                        is_a_exception, epoch = is_exception(all_settings, ioc, events_on_misp[event])

                        try:
                            epoch = int(epoch)
                            if epoch > 0 and epoch > int(ioc['timestamp']):
                                date_time = datetime.datetime.fromtimestamp(epoch)
                                attribute_timestamp = date_time.strftime(DATE_TIME_FORMAT)
                        except Exception:
                            pass

                        hash_string = '{}{}{}{}{}{}{}{}'.format(ioc_type, value, attribute_timestamp, str(ioc['comment']),
                                                                str(ioc['to_ids']), str(tags), str(epoch),
                                                                str(is_a_exception))
                        md5 = hashlib.md5(hash_string.encode('utf-8')).hexdigest()

                        ioc_count += 1

                        if ioc_type in IP_TYPES:
                            if not is_ipv4(value) and not is_ipv6(value):
                                continue

                        if ioc_type in HASH_TYPES:
                            if is_ipv4(value) or is_ipv6(value) or maybe_a_file(value):
                                continue

                        search_ioc = []
                        search_ioc.clear()
                        search_ioc = sqlite_command(all_settings, SQL_TO_GET_IOC_BY_MD5, (md5,))[1]

                        date_only = datetime.datetime.strptime(attribute_timestamp.split(' ')[0], DATE_FORMAT)
                        lived_days = calc_lived_days(date_only, 0)

                        today_date = datetime.datetime.strftime(datetime.datetime.now(), DATE_FORMAT)

                        if date_only.strftime(DATE_FORMAT) == today_date:
                            last_sync_timestamp = datetime.datetime.strftime(datetime.datetime.now(), DATE_TIME_FORMAT)
                        else:
                            last_sync_timestamp = body_by_type['from']

                        if len(search_ioc) == 0:
                            already_exists = sqlite_command(all_settings, SQL_TO_GET_IOC_BEFORE_DELETE, (ioc_type, value))
                            already_exists = len(already_exists[1])

                            sqlite_command(all_settings, SQL_TO_DELETE_IOC_BEFORE_EXCEPTION, (ioc_type, value))
                            success_count += 1

                            if is_a_exception and already_exists:
                                insert_status = sqlite_command(all_settings, SQL_TO_ADD_IOC_EXCEPTION, (ioc_type, value,
                                                                                          last_sync_timestamp,
                                                                                          attribute_timestamp, md5,
                                                                                          lived_days))[0]

                                database_updates += 1
                                ioc_update += 1

                                message = '{} count="{}/{}/{}" ' \
                                          'details="Add to local database to be ' \
                                          'purged in SIEM" value="{}"'.format(step_timestamp,
                                                                              str(ioc_count).zfill(4),
                                                                              str(len(iocs_from_misp)).zfill(4),
                                                                              str(database_updates).zfill(4),
                                                                              value.encode('ascii', 'ignore').decode('utf-8'))
                                logging.debug(message)

                            elif not is_a_exception:
                                insert_status = sqlite_command(all_settings, SQL_TO_ADD_IOC, (ioc_type, value, last_sync_timestamp,
                                                                                attribute_timestamp, md5,
                                                                                lived_days))[0]

                                database_updates += 1
                                ioc_update += 1

                                message = '{} count="{}/{}/{}" ' \
                                          'details="Add to local database to be synced ' \
                                          'with SIEM" value="{}"'.format(step_timestamp, str(ioc_count).zfill(4),
                                                                         str(len(iocs_from_misp)).zfill(4),
                                                                         str(database_updates).zfill(4),
                                                                         value.encode('ascii', 'ignore').decode('utf-8'))
                                logging.debug(message)
                            else:
                                insert_status = True

                            if not insert_status:
                                message = '{} count="{}/{}/{}" details="Error when add to" ' \
                                          'value="local database" value="{}"'.format(step_timestamp,
                                                                                     str(ioc_count).zfill(4),
                                                                                     str(len(iocs_from_misp)).zfill(4),
                                                                                     str(database_updates).zfill(4),
                                                                                     value.encode('ascii', 'ignore').decode('utf-8'))
                                logging.error(message)

                        sqlite_command(all_settings, SQL_TO_UPDATE_LAST_SYNC, (body_by_type['to'], ioc_type_settings))

                        progress = progress_logging(all_settings, len(iocs_from_misp), ioc_count)

                        if progress is not None:
                            message = '{} count="{}/{}/{}" details="Adding IOCs to local database" ' \
                                      'value="{}"'.format(step_timestamp, str(ioc_count).zfill(4),
                                                          str(len(iocs_from_misp)).zfill(4),
                                                          str(database_updates).zfill(4), progress)
                            logging.info(message)

                    reflect_db_to_siem(all_settings, execution_id)

                    if ioc_update == 0 and ioc_count > 0:
                        message = '{} details="Get IOCs but no changes" value="{}"'.format(step_timestamp, ioc_count)

                        logging.info(message)

                    elif len(iocs_from_misp) < 1:
                        message = '{} details="No IOCs found" value="{}"'.format(step_timestamp, len(iocs_from_misp))

                        logging.info(message)

                        sqlite_command(all_settings, SQL_TO_UPDATE_LAST_SYNC, (body_by_type['from'], ioc_type_settings))

            message = 'details="Ending loop for" value="{}"'.format(ioc_type_settings)
            logging.info(message)

            reflect_db_to_siem(all_settings, execution_id)

            sqlite_command(all_settings, SQL_TO_UPDATE_LAST_SYNC, (datetime.datetime.now().strftime(DATE_TIME_FORMAT),
                                                     ioc_type_settings))

        if success_count > 0:
            message = 'mode="{}" details="Updates in local database from MISP" value="{}"'.format(mode,
                                                                                                  database_updates)
        else:
            message = 'mode="{}" details="No new updates in local database from MISP" ' \
                      'value="{}"'.format(mode, database_updates)

        # Adjust lived days of each IOCs in local database
        update_lived_days(all_settings, mode)

        final_status = '{}\n{}'.format(final_status, message)
        logging.info(message)

        execution_stop_register(all_settings, execution_id, final_status.strip())
        return events_count_by_type

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        a = '{} - {}:{}'.format(e, fname, exc_tb.tb_lineno)
        execution_stop_register(all_settings, execution_id, a)
        return events_count_by_type
