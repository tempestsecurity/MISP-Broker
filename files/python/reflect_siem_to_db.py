import datetime
import logging
from files.python.constants import SQL_TO_LIST_ALL_IOCS_NOT_FALSE_POSITIVE, SQL_TO_UPDATE_IOC_AS_FALSE_POSITIVE, \
    DATE_TIME_FORMAT
from files.python.csv import csv_list_data, csv_delete_item
from files.python.global_functions import get_type_and_feed_lists, check_status_code, generate_siem_storage_name, progress_logging
from files.python.qradar import qradar_list_data, qradar_delete_item
from files.python.splunk import splunk_list_data, splunk_search_ioc, splunk_delete_item
from files.python.sqlite_functions import sqlite_command


def mark_as_false_positive(all_settings, execution_id):
    type_list, custom_feed = get_type_and_feed_lists(all_settings, execution_id)
    counter_limit = 0
    max_limit = 100
    type_count = 0

    for ioc_type in type_list:

        type_count += 1
        
        message = 'mode="AGENT" details="Checking {} IOCs status" value="{}/{}"'.format(ioc_type, type_count, len(type_list))
        logging.info(message)

        comparator = '='
        type_ttl = int(type_list[ioc_type]['ttl'])
        type_element_type = type_list[ioc_type]['element_type']

        if type_ttl == 0:
            type_ttl = 365000

        try:
            total_by_type_in_db = sqlite_command(all_settings, SQL_TO_LIST_ALL_IOCS_NOT_FALSE_POSITIVE, (ioc_type, type_ttl))

            ioc_list = []
            siem_list = []

            for ioc in total_by_type_in_db[1]:
                if type_element_type == 'ALNIC':
                    ioc_list.append(str(ioc[0]).strip().lower())
                    comparator = 'like'
                else:
                    ioc_list.append(str(ioc[0]).strip())

            if all_settings['SIEM_SETTINGS']['SIEM'] == 'QRADAR':
                total_by_type_in_siem = qradar_list_data(all_settings, generate_siem_storage_name(all_settings, ioc_type))

                for ioc in total_by_type_in_siem['data']:
                    siem_list.append(str(ioc['value']).strip())

            elif all_settings['SIEM_SETTINGS']['SIEM'] == 'SPLUNK':
                siem_list = splunk_list_data(all_settings, generate_siem_storage_name(all_settings, ioc_type))

            elif all_settings['SIEM_SETTINGS']['SIEM'] == 'CSV':
                siem_list = csv_list_data(all_settings, generate_siem_storage_name(all_settings, ioc_type))

            ioc_list.sort()
            siem_list.sort()

            if len(siem_list) < len(ioc_list):

                count = 0
                count_progress = 0
                
                for item in ioc_list:
                    
                    count_progress += 1
                    
                    progress = progress_logging(all_settings, len(ioc_list), count_progress)
                    
                    if progress is not None:
                        message = 'mode="AGENT" details="Checking {} IOCs from {} in DB" value="{} ({}/{})"'.format(ioc_type, all_settings['SIEM_SETTINGS']['SIEM'], progress, count_progress, len(ioc_list))
                        logging.info(message)
                    
                    if item not in siem_list:

                        now = datetime.datetime.now()
                        now = now.strftime(DATE_TIME_FORMAT)

                        sqlite_command(all_settings, SQL_TO_UPDATE_IOC_AS_FALSE_POSITIVE.format(comparator),
                                       (now, ioc_type, type_ttl, item))
                        count += 1
                        counter_limit += 1

                        message = 'details="Marked as false-positive in DB ({}/{})" ' \
                                  'type="{}" value="{}"'.format(count, len(ioc_list), ioc_type,
                                                                item.encode('ascii', 'ignore').decode('utf-8'))
                        logging.info(message)

                        if counter_limit >= max_limit:
                            break

            elif len(siem_list) > len(ioc_list):

                count = 0
                count_progress = 0

                for item in siem_list:
                    
                    count_progress += 1
                    
                    progress = progress_logging(all_settings, len(ioc_list), count_progress)
                    
                    if progress is not None:
                        message = 'details="Checking {} IOCs from DB in {}" value="{} ({}/{})"'.format(ioc_type, all_settings['SIEM_SETTINGS']['SIEM'], progress, count_progress, len(ioc_list))
                        logging.info(message)
                    
                    if item not in ioc_list:

                        post_status, post_text = '000', 'error'

                        siem_storage = generate_siem_storage_name(all_settings, ioc_type)
                        
                        if all_settings['SIEM_SETTINGS']['SIEM'] == 'QRADAR':
                            post_status, post_text = qradar_delete_item(all_settings, siem_storage, item)

                        elif all_settings['SIEM_SETTINGS']['SIEM'] == 'SPLUNK':
                            for key in splunk_search_ioc(all_settings, siem_storage, item):
                                post_status, post_text = splunk_delete_item(all_settings, siem_storage, key)

                        elif all_settings['SIEM_SETTINGS']['SIEM'] == 'CSV':
                            post_status, post_text = csv_delete_item(all_settings, siem_storage)

                        if all_settings['SIEM_SETTINGS']['SIEM'] == 'CSV':
                            count += 1
                            counter_limit += 1
                            message = 'details="Removed the IOC from database because was removed from {} ' \
                                      'by another source" count="{}" ' \
                                      'type="{}" value="{}"'.format(all_settings['SIEM_SETTINGS']['SIEM'], count, siem_storage,
                                                                    item.encode('ascii', 'ignore').decode('utf-8'))
                            logging.info(message)
                        elif check_status_code(post_status) or check_status_code(post_status, 4):
                            count += 1
                            counter_limit += 1
                            message = 'details="Removed the IOC from database because was removed from {} ' \
                                      'by another source" count="{}" ' \
                                      'type="{}" value="{}"'.format(all_settings['SIEM_SETTINGS']['SIEM'], count, ioc_type,
                                                                    item.encode('ascii', 'ignore').decode('utf-8'))
                            logging.info(message)
                        else:
                            message = 'details="Error while try to remove the IOC from database because ' \
                                      'was removed from {} - ' \
                                      '{}, {}" count="{}" type="{}" value="{}"'.format(all_settings['SIEM_SETTINGS']['SIEM'],
                                                                                       post_status, post_text,
                                                                                       count, ioc_type,
                                                                                       item.encode('ascii', 'ignore').decode('utf-8'))
                            logging.error(message)

                        if counter_limit >= max_limit:
                            break

        except Exception:
            continue

    return None
