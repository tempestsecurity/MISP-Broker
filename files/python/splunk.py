import json
import logging
import os
import re
import shutil
import tarfile
import time
import requests
from files.python.constants import SQL_TO_ADD_SIEM_STORAGE_IN_DB, SQL_TO_UPDATE_LAST_SYNC_SIEM_STORAGE, SQL_TO_CHECK_SYNCED_IOC, SQL_TO_GET_ALL_KV_NAMES
from files.python.global_functions import generate_siem_storage_name, check_status_code, check_siem_storage_in_db, \
    check_run_status, get_type_and_feed_lists, progress_logging
from files.python.sqlite_functions import sqlite_command


def splunk_app_generator(all_settings):
    type_list, custom_feed = get_type_and_feed_lists(all_settings, '0')

    try:
        shutil.rmtree(all_settings['SIEM_SETTINGS']['APP_DIR'])
    except Exception:
        pass

    os.mkdir(all_settings['SIEM_SETTINGS']['APP_DIR'])
    os.mkdir('{}/default'.format(all_settings['SIEM_SETTINGS']['APP_DIR']))
    os.mkdir('{}/metadata'.format(all_settings['SIEM_SETTINGS']['APP_DIR']))

    with open(all_settings['SIEM_SETTINGS']['APP_FILE'], 'w') as f:
        f.write(all_settings['SIEM_SETTINGS']['APP_CONF'])

    for ioc_type in type_list:
        kv_name = generate_siem_storage_name(all_settings, ioc_type)
        kv_element_type = splunk_get_element_type(all_settings, type_list[ioc_type]['element_type'])

        with open(all_settings['SIEM_SETTINGS']['COLLECTIONS_FILE'], 'a') as f:
            f.write('[{}]\n'.format(kv_name))
            f.write('field.value = {}\n\n'.format(kv_element_type))

        with open(all_settings['SIEM_SETTINGS']['TRANSFORMS_FILE'], 'a') as f:
            f.write('[{}]\n'.format(kv_name))
            f.write('collection = {}\n'.format(kv_name))
            f.write('external_type = kvstore\n')
            f.write('fields_list = value, _key\n\n')

    with open(all_settings['SIEM_SETTINGS']['META_FILE'], 'w') as f:
        f.write(all_settings['SIEM_SETTINGS']['DEFAULT_META'])

    tar = tarfile.open('{}_{}.tar.gz'.format(all_settings['SIEM_SETTINGS']['APP_DIR'], all_settings['SIEM_SETTINGS']['SIEM_APP_VERSION']), 'w:gz')
    for name in [all_settings['SIEM_SETTINGS']['APP_FILE'], all_settings['SIEM_SETTINGS']['COLLECTIONS_FILE'], all_settings['SIEM_SETTINGS']['TRANSFORMS_FILE'], all_settings['SIEM_SETTINGS']['META_FILE']]:
        tar.add(name)
    tar.close()

    try:
        shutil.rmtree(all_settings['SIEM_SETTINGS']['APP_DIR'])
    except Exception:
        pass


def splunk_get_element_type(all_settings, element_type):
    if str(element_type).upper() in all_settings['SIEM_SETTINGS']['SPLUNK_ELEMENT_TYPE_STRING']:
        return 'string'
    elif str(element_type).upper() in all_settings['SIEM_SETTINGS']['SPLUNK_ELEMENT_TYPE_CIDR']:
        return 'cidr'
    elif str(element_type).upper() in all_settings['SIEM_SETTINGS']['SPLUNK_ELEMENT_TYPE_NUMBER']:
        return 'number'
    else:
        return 'string'


def splunk_list_all_kv(all_settings):
    # Loads a list to existing reference set
    get_data = requests.get(all_settings['SIEM_SETTINGS']['SPLUNK_KV_CONFIG_URL'], data=all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'], headers=all_settings['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=all_settings['SIEM_SETTINGS']['SIEM_VERIFY_SSL'])

    dict_data = get_data.json()
    kv_list = []

    for kv in dict_data['entry']:

        if re.findall(r'{}'.format(generate_siem_storage_name(all_settings)), kv['name']):
            kv_list.append(kv['name'])

    return get_data.status_code, get_data.text


def splunk_create_kv(all_settings, element_type, kv_name):
    post_data = requests.post(all_settings['SIEM_SETTINGS']['SPLUNK_KV_CONFIG_URL'], data='name={}'.format(kv_name), headers=all_settings['SIEM_SETTINGS']['SPLUNK_HEADERS'],
                              verify=all_settings['SIEM_SETTINGS']['SIEM_VERIFY_SSL'])

    if check_status_code(post_data.status_code):
        post_data = requests.post('{}/{}'.format(all_settings['SIEM_SETTINGS']['SPLUNK_KV_CONFIG_URL'], kv_name),
                                  data='field.value={}'.format(element_type),
                                  headers=all_settings['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=all_settings['SIEM_SETTINGS']['SIEM_VERIFY_SSL'])

    return post_data.status_code, post_data.text


def splunk_load(all_settings, kv_name, data_list):

    max_amount = 1000
    if all_settings['SIEM_SETTINGS']['BATCH_LIST_SIZE'] != '':
        try:
            max_amount = int(all_settings['SIEM_SETTINGS']['BATCH_LIST_SIZE'])
        except Exception:
            max_amount = 1000
    count = 0
    split_data_list = []

    status_code = 200
    data_text = 'already synced, not to do'

    for index in range(0, len(data_list), max_amount):
        split_data_list.append(data_list[index: index + max_amount])

    for splitter_list in split_data_list:

        batch_list = []
        count += 1

        message = 'count="{}/{}" details="Generating the batch list for {}" max_amount="{}"'.format(count, str(len(split_data_list)), kv_name, max_amount)
        logging.info(message)

        for item in splitter_list:
            batch_list.append({"value": "{}".format(item)})

        message = 'count="{}/{}" details="Finished the batch list for {}" appended="{}"'.format(count, str(len(split_data_list)), kv_name, str(len(batch_list)))
        logging.info(message)

        if len(batch_list) > 0:

            message = 'count="{}/{}" details="Posting the {} batch list to SPLUNK" size="{}"'.format(count, str(len(split_data_list)), kv_name, str(len(batch_list)))
            logging.info(message)

            post_data = requests.post(all_settings['SIEM_SETTINGS']['SPLUNK_KV_BATCH_URL'].format(kv_name), data=json.dumps(batch_list),
                                    headers=all_settings['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=all_settings['SIEM_SETTINGS']['SIEM_VERIFY_SSL'])

            status_code = post_data.status_code
            data_text = post_data.text

            if check_status_code(post_data.status_code):
                message = 'count="{}/{}" details="Post successfully the {} batch list to SPLUNK" posted="{}" status_code="{}"'.format(count, str(len(split_data_list)), kv_name, str(len(batch_list)), status_code)
                logging.info(message)
            else:
                message = 'count="{}/{}" details="Post ERROR in the {} batch list to SPLUNK" post_count="{}" status_code="{}" status_text="{}" post_data="{}"'.format(count, str(len(split_data_list)), kv_name, str(len(batch_list)), status_code, data_text, json.dumps(batch_list))
                logging.error(message)
                time.sleep(2)
                return status_code, data_text
            
            splunk_dedup_kv(all_settings, kv_name)

        else:
            return status_code, data_text

    return status_code, data_text


def splunk_search_ioc(all_settings, kv_name, value):
    all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE']['search'] = all_settings['SIEM_SETTINGS']['SPLUNK_QUERY_SEARCH_IOC'].format(kv_name, value)
    post_data = requests.post(all_settings['SIEM_SETTINGS']['SPLUNK_SEARCH_URL'], data=all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'], headers=all_settings['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=all_settings['SIEM_SETTINGS']['SIEM_VERIFY_SSL'])
    all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'].pop('search')

    dict_data = []
    for result in post_data.text.split('\n'):
        if result:
            try:
                dict_data.append(json.loads(result)['result']['view_key'])
            except Exception:
                pass

    return dict_data


def splunk_dedup_kv(all_settings, kv_name):
    all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE']['search'] = all_settings['SIEM_SETTINGS']['SPLUNK_DEDUP_SEARCH'].format(kv_name, kv_name)
    post_data = requests.post(all_settings['SIEM_SETTINGS']['SPLUNK_SEARCH_URL'], data=all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'], headers=all_settings['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=all_settings['SIEM_SETTINGS']['SIEM_VERIFY_SSL'])
    all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'].pop('search')
        
    status_code = post_data.status_code
    data_text = post_data.text

    if check_status_code(post_data.status_code):
        message = 'details="Dedup successfully in the {} KV on SPLUNK" status_code="{}"'.format(kv_name, status_code)
        logging.info(message)
    else:
        message = 'details="Dedup ERROR in the {} KV on SPLUNK" status_code="{}" status_text="{}"'.format(kv_name, status_code, data_text)
        logging.error(message)


def splunk_dedup_kvs(all_settings):
    kv_list = sqlite_command(all_settings, SQL_TO_GET_ALL_KV_NAMES)[1]
    
    count = 0
    for kv in kv_list:
        count += 1
        kv_name = kv[0]
        all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE']['search'] = all_settings['SIEM_SETTINGS']['SPLUNK_DEDUP_SEARCH'].format(kv_name, kv_name)
        post_data = requests.post(all_settings['SIEM_SETTINGS']['SPLUNK_SEARCH_URL'], data=all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'], headers=all_settings['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=all_settings['SIEM_SETTINGS']['SIEM_VERIFY_SSL'])
        all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'].pop('search')
            
        status_code = post_data.status_code
        data_text = post_data.text

        if check_status_code(post_data.status_code):
            message = 'count="{}/{}" details="Dedup successfully in the {} KV on SPLUNK" status_code="{}"'.format(count, str(len(kv_list)), kv_name, status_code)
            logging.info(message)
        else:
            message = 'count="{}/{}" details="Dedup ERROR in the {} KV on SPLUNK" status_code="{}" status_text="{}"'.format(count, str(len(kv_list)), kv_name, status_code, data_text)
            logging.error(message)
        


def splunk_delete_item(all_settings, kv_name, key):
    url_kv = all_settings['SIEM_SETTINGS']['SPLUNK_KV_DATA_URL'].format(kv_name)
    delete_data = requests.delete('{}/{}'.format(url_kv, key), data=all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'],
                                  headers=all_settings['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=all_settings['SIEM_SETTINGS']['SIEM_VERIFY_SSL'])

    return delete_data.status_code, delete_data.text


def splunk_purge_kv(all_settings, kv_name):
    delete_data = requests.delete(all_settings['SIEM_SETTINGS']['SPLUNK_KV_DATA_URL'].format(kv_name), data=all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'],
                                  headers=all_settings['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=all_settings['SIEM_SETTINGS']['SIEM_VERIFY_SSL'])

    return delete_data.status_code, delete_data.text


def splunk_list_data(all_settings, kv_name):
    get_data = requests.get(all_settings['SIEM_SETTINGS']['SPLUNK_KV_DATA_URL'].format(kv_name), data=all_settings['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'],
                            headers=all_settings['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=all_settings['SIEM_SETTINGS']['SIEM_VERIFY_SSL'])
    data_list = []
    try:
        for item in get_data.json():
            data_list.append(item['value'])
    except Exception:
        pass

    return get_data.status_code, data_list


def splunk_add_to_kv(all_settings, ioc_type, element_type, update_time, data_list, execution_id):
    kv_name = generate_siem_storage_name(all_settings, ioc_type)
    element_type = splunk_get_element_type(all_settings, element_type)

    post_status, post_text = '001', 'error in splunk_add_to_kv function'

    if not check_siem_storage_in_db(all_settings, ioc_type):
        message = 'mode="AGENT" type="{}" details="Creating KV Store in SPLUNK" ' \
                  'value="{}"'.format(ioc_type, kv_name)
        # print(message)
        logging.info(message)

        post_status, post_text = splunk_create_kv(all_settings, kv_name, element_type)

        already_in_use = re.findall(all_settings['SIEM_SETTINGS']['SPLUNK_ALREADY_IN_USE'], post_text)

        if check_status_code(post_status) or already_in_use:
            sqlite_command(all_settings, SQL_TO_ADD_SIEM_STORAGE_IN_DB, (ioc_type, kv_name, 1, update_time))

            message = 'mode="AGENT" type="{}" details="Created KV Store in SPLUNK" ' \
                      'value="{} - {} - {}"'.format(ioc_type, kv_name, post_status, post_text)
            logging.info(message)
        else:
            message = 'mode="AGENT" type="{}" details="Error while try to create KV Store in SPLUNK" ' \
                      'value="{} - {} - {}"'.format(ioc_type, kv_name, post_status, post_text)
            logging.error(message)
    else:
        post_status, post_text = splunk_load(all_settings, kv_name, data_list)

        if check_status_code(post_status):
            sqlite_command(all_settings, SQL_TO_UPDATE_LAST_SYNC_SIEM_STORAGE, (update_time, ioc_type))

    check_run_status(all_settings, execution_id)

    return post_status, post_text
