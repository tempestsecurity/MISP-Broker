import datetime
import logging
import re
from files.python.constants import SQL_TO_LIST_IOCS, SQL_TO_LIST_TYPES_IN_DB, DATE_TIME_FORMAT, SQL_TO_UPDATE_PURGED_ITEM, \
    SQL_TO_LIST_ITEM_TO_REMOVE, SQL_TO_UPDATE_ADD_ITEM, SQL_TO_UPDATE_PURGED_TYPE, SQL_TO_UPDATE_PURGED_SIEM_STORAGE, SQL_TO_ADD_SIEM_STORAGE_IN_DB
from files.python.csv import csv_create, csv_purge_csv, csv_add_to_file, csv_delete_item
from files.python.global_functions import get_type_and_feed_lists, progress_logging, check_status_code, \
    check_siem_storage_in_db, generate_siem_storage_name
from files.python.qradar import qradar_purge_reference_set, qradar_delete_item, qradar_add_to_reference_set, \
    qradar_create_refence_set
from files.python.splunk import splunk_create_kv, splunk_add_to_kv, splunk_purge_kv, splunk_delete_item, \
    splunk_search_ioc, splunk_app_generator
from files.python.sqlite_functions import sqlite_command, execution_stop_register


def create_store_in_siem(all_settings, execution_id):
    type_list, custom_feed = get_type_and_feed_lists(all_settings, execution_id)

    post_status, post_text = '001', 'error in create_store_in_siem function'
    already_in_use = False
    has_new = False
    kv_items = []

    for ioc_type in type_list:
        siem_storage = generate_siem_storage_name(all_settings, ioc_type)
        type_ttl = int(type_list[ioc_type]['ttl'])
        type_element_type = type_list[ioc_type]['element_type']

        if not check_siem_storage_in_db(all_settings, ioc_type):
            message = 'mode="AGENT" type="{}" details="Creating storage name in {}" ' \
                      'value="{}"'.format(ioc_type, all_settings['SIEM_SETTINGS']['SIEM'], siem_storage)

            logging.info(message)

            if all_settings['SIEM_SETTINGS']['SIEM'] == 'QRADAR':
                post_status, post_text = qradar_create_refence_set(all_settings, type_element_type, siem_storage, type_ttl)
                already_in_use = re.findall(all_settings['SIEM_SETTINGS']['QRADAR_ALREADY_IN_USE'], post_text)

                qradar_purge_reference_set(all_settings, siem_storage)

            elif all_settings['SIEM_SETTINGS']['SIEM'] == 'SPLUNK':
                post_status, post_text = '200', 'create app'
                splunk_app_generator(all_settings)
                already_in_use = re.findall(all_settings['SIEM_SETTINGS']['SPLUNK_ALREADY_IN_USE'], post_text)
                kv_items.append(siem_storage)

                splunk_purge_kv(all_settings, siem_storage)

            elif all_settings['SIEM_SETTINGS']['SIEM'] == 'CSV':
                csv_purge_csv(all_settings, siem_storage)
                post_status, post_text = csv_create(all_settings, siem_storage)


            if check_status_code(post_status) or already_in_use:

                now = datetime.datetime.now()
                now = now.strftime(DATE_TIME_FORMAT)

                sqlite_command(all_settings, SQL_TO_ADD_SIEM_STORAGE_IN_DB, (ioc_type, siem_storage, 1, now))

                message = 'mode="AGENT" type="{}" details="Created reference set in {}" ' \
                          'value="{} - {} - {}"'.format(ioc_type, all_settings['SIEM_SETTINGS']['SIEM'], siem_storage, post_status, post_text)
                logging.info(message)

                has_new = True
            else:
                message = 'mode="AGENT" type="{}" details="Error while try to create reference set in {}" ' \
                      'value="{} - {} - {}"'.format(ioc_type, all_settings['SIEM_SETTINGS']['SIEM'], siem_storage, post_status, post_text)
                logging.error(message)

    if all_settings['SIEM_SETTINGS']['SIEM'] == 'SPLUNK' and has_new:
        message = 'mode="AGENT" details="App created, please, now go to the {} and install the app." ' \
                  'value="{}_v{}.tar.gz"'.format(all_settings['SIEM_SETTINGS']['SIEM'], all_settings['SIEM_SETTINGS']['APP_DIR'], all_settings['SIEM_SETTINGS']['SIEM_APP_VERSION'])
        logging.warning(message)

        message = 'App created, please, now go to the {} and install the app {}_v{}.tar.gz'.format(all_settings['SIEM_SETTINGS']['SIEM'], all_settings['SIEM_SETTINGS']['APP_DIR'], all_settings['SIEM_SETTINGS']['SIEM_APP_VERSION'])
        execution_stop_register(all_settings, execution_id, message)
        print(message)
        quit()

    return post_status, post_text


def add_to_siem(all_settings, execution_id):
    type_list, custom_feed = get_type_and_feed_lists(all_settings, execution_id)

    for ioc_type in type_list:
        type_ttl = int(type_list[ioc_type]['ttl'])
        type_element_type = type_list[ioc_type]['element_type']

        # Try to get the time to live for this IOC, if is not configured then use the default in settings
        try:
            if type_ttl == 0:
                type_ttl = 365000

            days = type_ttl
        except Exception:
            days = int(all_settings['BROKER_SETTINGS']['DEFAULT_TTL'])

        ioc_list = sqlite_command(all_settings, SQL_TO_LIST_IOCS, (days, ioc_type))[1]
        data_list = []

        for ioc in ioc_list:
            data_list.append(ioc[2])

        if data_list:

            now = datetime.datetime.now()
            now = now.strftime(DATE_TIME_FORMAT)

            post_status, post_text = '000', 'error'

            message = 'details="Sending to {}" type="{}" element_type="{}" ttl_days="{}" timestamp="{}" ' \
                      'value="{}"'.format(all_settings['SIEM_SETTINGS']['SIEM'], ioc_type, type_element_type,
                                          days, now, len(data_list))
            logging.info(message)

            if all_settings['SIEM_SETTINGS']['SIEM'] == 'QRADAR':
                post_status, post_text = qradar_add_to_reference_set(all_settings, ioc_type, type_element_type, days, now,
                                                                     data_list, execution_id)

            elif all_settings['SIEM_SETTINGS']['SIEM'] == 'SPLUNK':
                post_status, post_text = splunk_add_to_kv(all_settings, ioc_type, type_element_type, now,
                                                          data_list, execution_id)

            elif all_settings['SIEM_SETTINGS']['SIEM'] == 'CSV':
                post_status, post_text = csv_add_to_file(all_settings, ioc_type, now, data_list, execution_id)

            if check_status_code(post_status):
                message = 'details="Sent to {}" type="{}" element_type="{}" ttl_days="{}" timestamp="{}" ' \
                          'value="{}"'.format(all_settings['SIEM_SETTINGS']['SIEM'], ioc_type, type_element_type,
                                              days, now, len(data_list))
                logging.info(message)
            else:
                message = 'details="While try to send to {}" type="{}" element_type="{}" ttl="{}" timestamp="{}" ' \
                          'value="{}"'.format(all_settings['SIEM_SETTINGS']['SIEM'], ioc_type, type_element_type,
                                              days, now, len(data_list))
                logging.error(message)

            if check_status_code(post_status):
                update_counter = 0

                for ioc in data_list:

                    sqlite_command(all_settings, SQL_TO_UPDATE_ADD_ITEM, (now, ioc_type, ioc))
                    update_counter += 1

                    message = 'details="Updating database" type="{}" element_type="{}" ttl="{}" timestamp="{}" ' \
                              'value="{}"'.format(ioc_type, type_element_type,
                                                  days, now, ioc)
                    logging.debug(message)


                    progress = progress_logging(all_settings, len(data_list), update_counter)

                    if progress is not None:
                        message = 'details="Updating database" count="{}/{}" ' \
                                  'value="{}"'.format(str(update_counter).zfill(4),
                                                      str(len(data_list)).zfill(4), progress)
                        logging.info(message)

    return None


def remove_type_from_siem(all_settings, execution_id):
    type_list, custom_feed = get_type_and_feed_lists(all_settings, execution_id)

    sqlite_command(all_settings, SQL_TO_LIST_TYPES_IN_DB)

    ioc_list = sqlite_command(all_settings, SQL_TO_LIST_TYPES_IN_DB)[1]
    data_list = []

    for ioc in ioc_list:
        data_list.append(ioc[0])

    for ioc_type in data_list:
        if ioc_type not in type_list:

            now = datetime.datetime.now()
            now = now.strftime(DATE_TIME_FORMAT)

            post_status, post_text = '000', 'error'

            siem_storage = generate_siem_storage_name(all_settings, ioc_type)

            if all_settings['SIEM_SETTINGS']['SIEM'] == 'QRADAR':
                post_status, post_text = qradar_purge_reference_set(all_settings, siem_storage)

            elif all_settings['SIEM_SETTINGS']['SIEM'] == 'SPLUNK':
                post_status, post_text = splunk_purge_kv(all_settings, siem_storage)

            elif all_settings['SIEM_SETTINGS']['SIEM'] == 'CSV':
                post_status, post_text = csv_purge_csv(all_settings, siem_storage)

            if check_status_code(post_status) or check_status_code(post_status, 4):
                sqlite_command(all_settings, SQL_TO_UPDATE_PURGED_TYPE, (now, ioc_type))
                sqlite_command(all_settings, SQL_TO_UPDATE_PURGED_SIEM_STORAGE, (now, ioc_type))
                message = 'details="Removed from {} the SIEM Storage" value="{}"'.format(all_settings['SIEM_SETTINGS']['SIEM'], siem_storage)
                logging.info(message)
            else:
                message = 'details="Error while try to remove from {} the SIEM Storage" ' \
                          'value="{}"'.format(all_settings['SIEM_SETTINGS']['SIEM'], siem_storage)
                logging.error(message)

    return None


def remove_ioc_from_siem(all_settings, execution_id):
    type_list, custom_feed = get_type_and_feed_lists(all_settings, execution_id)

    for ioc_type in type_list:

        if check_siem_storage_in_db(all_settings, ioc_type):

            type_ttl = int(type_list[ioc_type]['ttl'])

            if type_ttl == 0:
                type_ttl = 365000

            ioc_list = sqlite_command(all_settings, SQL_TO_LIST_ITEM_TO_REMOVE, (ioc_type, type_ttl))[1]
            data_list = {'false-positive': [], 'expired': []}

            for ioc in ioc_list:
                if ioc[4] == 1:
                    data_list['false-positive'].append(ioc[2])
                else:
                    data_list['expired'].append(ioc[2])

            for reason in data_list:

                count = 0
                total = len(data_list[reason])

                if data_list[reason]:

                    for item in data_list[reason]:

                        now = datetime.datetime.now()
                        now = now.strftime(DATE_TIME_FORMAT)

                        post_status, post_text = '200', 'not to do'

                        siem_storage = generate_siem_storage_name(all_settings, ioc_type)

                        if all_settings['SIEM_SETTINGS']['SIEM'] == 'QRADAR':
                            post_status, post_text = qradar_delete_item(all_settings, siem_storage, item)

                        elif all_settings['SIEM_SETTINGS']['SIEM'] == 'SPLUNK':
                            for key in splunk_search_ioc(all_settings, siem_storage, item):
                                post_status, post_text = splunk_delete_item(all_settings, siem_storage, key)

                        elif all_settings['SIEM_SETTINGS']['SIEM'] == 'CSV':
                            post_status, post_text = csv_delete_item(all_settings, siem_storage, item)

                        if check_status_code(post_status) or check_status_code(post_status, 4):
                            sqlite_command(all_settings, SQL_TO_UPDATE_PURGED_ITEM, (now, ioc_type, item))
                            count += 1

                            message = 'details="Removed from {} the IOC because is {} ({}/{})" ' \
                                      'type="{}" value="{}"'.format(all_settings['SIEM_SETTINGS']['SIEM'], reason, count, total,
                                                                    ioc_type,
                                                                    item.encode('ascii', 'ignore').decode('utf-8'))
                            logging.debug(message)
                        else:
                            message = 'details="Error while try to remove from {} the IOC because is {} ' \
                                      '({}/{}) - ' \
                                      '{}, {}" type="{}" value="{}"'.format(all_settings['SIEM_SETTINGS']['SIEM'], reason, count, total,
                                                                            post_status, post_text, ioc_type,
                                                                            item.encode('ascii', 'ignore').decode('utf-8'))
                            logging.error(message)

                        progress = progress_logging(all_settings, total, count)

                        if progress is not None:
                            message = 'mode="AGENT" details="Removing {} {} IOCs ' \
                                      'from SIEM" value="{} ({}/{})"'.format(reason, ioc_type, progress, count, total)
                            logging.info(message)

    return None


def reflect_db_to_siem(all_settings, execution_id):
    logging.debug("Starting: create_store_in_siem")
    create_store_in_siem(all_settings, execution_id)
    logging.debug("Ending: create_store_in_siem")
    logging.debug("Starting: add_to_siem")
    add_to_siem(all_settings, execution_id)
    logging.debug("Ending: add_to_siem")
    logging.debug("Starting: remove_type_from_siem")
    remove_type_from_siem(all_settings, execution_id)
    logging.debug("Ending: remove_type_from_siem")
    logging.debug("Starting: remove_ioc_from_siem")
    remove_ioc_from_siem(all_settings, execution_id)
    logging.debug("Ending: remove_ioc_from_siem")

    return None
