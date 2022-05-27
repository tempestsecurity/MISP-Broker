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


def splunk_app_generator(SETTINGS):
    type_list, custom_feed = get_type_and_feed_lists(SETTINGS, '0')

    try:
        shutil.rmtree(SETTINGS['SIEM_SETTINGS']['APP_DIR'])
    except:
        pass

    os.mkdir(SETTINGS['SIEM_SETTINGS']['APP_DIR'])
    os.mkdir('{}/default'.format(SETTINGS['SIEM_SETTINGS']['APP_DIR']))
    os.mkdir('{}/metadata'.format(SETTINGS['SIEM_SETTINGS']['APP_DIR']))

    with open(SETTINGS['SIEM_SETTINGS']['APP_FILE'], 'w') as f:
        f.write(SETTINGS['SIEM_SETTINGS']['APP_CONF'])

    for ioc_type in type_list:
        kv_name = generate_siem_storage_name(SETTINGS, ioc_type)
        kv_element_type = splunk_get_element_type(SETTINGS, type_list[ioc_type]['element_type'])

        with open(SETTINGS['SIEM_SETTINGS']['COLLECTIONS_FILE'], 'a') as f:
            f.write('[{}]\n'.format(kv_name))
            f.write('field.value = {}\n\n'.format(kv_element_type))

        with open(SETTINGS['SIEM_SETTINGS']['TRANSFORMS_FILE'], 'a') as f:
            f.write('[{}]\n'.format(kv_name))
            f.write('collection = {}\n'.format(kv_name))
            f.write('external_type = kvstore\n')
            f.write('fields_list = value, _key\n\n')

    #with open(LIMITS_FILE, 'w') as f:
        #f.write('[kvstore]\n')
        #f.write('max_documents_per_batch_save = 20000000\n')
        #f.write('max_size_per_batch_save_mb = 20000\n')

    with open(SETTINGS['SIEM_SETTINGS']['META_FILE'], 'w') as f:
        f.write(SETTINGS['SIEM_SETTINGS']['DEFAULT_META'])

    tar = tarfile.open('{}_{}.tar.gz'.format(SETTINGS['SIEM_SETTINGS']['APP_DIR'], SETTINGS['SIEM_SETTINGS']['SIEM_APP_VERSION']), 'w:gz')
    for name in [SETTINGS['SIEM_SETTINGS']['APP_FILE'], SETTINGS['SIEM_SETTINGS']['COLLECTIONS_FILE'], SETTINGS['SIEM_SETTINGS']['TRANSFORMS_FILE'], SETTINGS['SIEM_SETTINGS']['META_FILE']]:
        tar.add(name)
    tar.close()

    try:
        shutil.rmtree(SETTINGS['SIEM_SETTINGS']['APP_DIR'])
    except:
        pass


def splunk_get_element_type(SETTINGS, element_type):
    if str(element_type).upper() in SETTINGS['SIEM_SETTINGS']['SPLUNK_ELEMENT_TYPE_STRING']:
        return 'string'
    elif str(element_type).upper() in SETTINGS['SIEM_SETTINGS']['SPLUNK_ELEMENT_TYPE_CIDR']:
        return 'cidr'
    elif str(element_type).upper() in SETTINGS['SIEM_SETTINGS']['SPLUNK_ELEMENT_TYPE_NUMBER']:
        return 'number'
    else:
        return 'string'


def splunk_list_all_kv(SETTINGS):
    # Loads a list to existing reference set
    get_data = requests.get(SETTINGS['SIEM_SETTINGS']['SPLUNK_KV_CONFIG_URL'], data=SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'], headers=SETTINGS['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=False)

    dict_data = get_data.json()
    kv_list = []

    for kv in dict_data['entry']:

        if re.findall(r'{}'.format(generate_siem_storage_name(SETTINGS)), kv['name']):
            kv_list.append(kv['name'])

    return get_data.status_code, get_data.text
    # return '200', 'post_text'


def splunk_create_kv(SETTINGS, element_type, kv_name):
    post_data = requests.post(SETTINGS['SIEM_SETTINGS']['SPLUNK_KV_CONFIG_URL'], data='name={}'.format(kv_name), headers=SETTINGS['SIEM_SETTINGS']['SPLUNK_HEADERS'],
                              verify=False)

    if check_status_code(post_data.status_code):
        post_data = requests.post('{}/{}'.format(SETTINGS['SIEM_SETTINGS']['SPLUNK_KV_CONFIG_URL'], kv_name),
                                  data='field.value={}'.format(element_type),
                                  headers=SETTINGS['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=False)

    return post_data.status_code, post_data.text


def splunk_load(SETTINGS, kv_name, data_list, ioc_type):

    max_amount = 1000
    if SETTINGS['SIEM_SETTINGS']['BATCH_LIST_SIZE'] != '':
        try:
            max_amount = int(SETTINGS['SIEM_SETTINGS']['BATCH_LIST_SIZE'])
        except:
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

            post_data = requests.post(SETTINGS['SIEM_SETTINGS']['SPLUNK_KV_BATCH_URL'].format(kv_name), data=json.dumps(batch_list),
                                    headers=SETTINGS['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=False)

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
            
            splunk_dedup_kv(SETTINGS, kv_name)

        else:
            return status_code, data_text

    return status_code, data_text


def splunk_search_ioc(SETTINGS, kv_name, value):
    # kv_name = generate_siem_storage_name(ioc_type)
    SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE']['search'] = SETTINGS['SIEM_SETTINGS']['SPLUNK_QUERY_SEARCH_IOC'].format(kv_name, value)
    post_data = requests.post(SETTINGS['SIEM_SETTINGS']['SPLUNK_SEARCH_URL'], data=SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'], headers=SETTINGS['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=False)
    SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'].pop('search')

    dict_data = []
    for result in post_data.text.split('\n'):
        if result:
            try:
                dict_data.append(json.loads(result)['result']['view_key'])
            except:
                pass

    return dict_data


def splunk_dedup_kv(SETTINGS, kv_name):
    SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE']['search'] = SETTINGS['SIEM_SETTINGS']['SPLUNK_DEDUP_SEARCH'].format(kv_name, kv_name)
    post_data = requests.post(SETTINGS['SIEM_SETTINGS']['SPLUNK_SEARCH_URL'], data=SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'], headers=SETTINGS['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=False)
    SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'].pop('search')
        
    status_code = post_data.status_code
    data_text = post_data.text

    if check_status_code(post_data.status_code):
        message = 'details="Dedup successfully in the {} KV on SPLUNK" status_code="{}"'.format(kv_name, status_code)
        logging.info(message)
    else:
        message = 'details="Dedup ERROR in the {} KV on SPLUNK" status_code="{}" status_text="{}"'.format(kv_name, status_code, data_text)
        logging.error(message)


def splunk_dedup_kvs(SETTINGS):
    # kv_name = generate_siem_storage_name(ioc_type)
    kv_list = sqlite_command(SETTINGS, SQL_TO_GET_ALL_KV_NAMES)[1]
    
    count = 0
    for kv in kv_list:
        count += 1
        kv_name = kv[0]
        SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE']['search'] = SETTINGS['SIEM_SETTINGS']['SPLUNK_DEDUP_SEARCH'].format(kv_name, kv_name)
        post_data = requests.post(SETTINGS['SIEM_SETTINGS']['SPLUNK_SEARCH_URL'], data=SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'], headers=SETTINGS['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=False)
        SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'].pop('search')
            
        status_code = post_data.status_code
        data_text = post_data.text

        if check_status_code(post_data.status_code):
            message = 'count="{}/{}" details="Dedup successfully in the {} KV on SPLUNK" status_code="{}"'.format(count, str(len(kv_list)), kv_name, status_code)
            logging.info(message)
        else:
            message = 'count="{}/{}" details="Dedup ERROR in the {} KV on SPLUNK" status_code="{}" status_text="{}"'.format(count, str(len(kv_list)), kv_name, status_code, data_text)
            logging.error(message)
        


def splunk_delete_item(SETTINGS, kv_name, key):
    # kv_name = generate_siem_storage_name(kv_name)
    url_kv = SETTINGS['SIEM_SETTINGS']['SPLUNK_KV_DATA_URL'].format(kv_name)
    delete_data = requests.delete('{}/{}'.format(url_kv, key), data=SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'],
                                  headers=SETTINGS['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=False)

    return delete_data.status_code, delete_data.text


def splunk_purge_kv(SETTINGS, kv_name):
    # kv_name = generate_siem_storage_name(kv_name)
    delete_data = requests.delete(SETTINGS['SIEM_SETTINGS']['SPLUNK_KV_DATA_URL'].format(kv_name), data=SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'],
                                  headers=SETTINGS['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=False)

    return delete_data.status_code, delete_data.text


def splunk_list_data(SETTINGS, kv_name):
    get_data = requests.get(SETTINGS['SIEM_SETTINGS']['SPLUNK_KV_DATA_URL'].format(kv_name), data=SETTINGS['SIEM_SETTINGS']['SPLUNK_OUTPUT_MODE'],
                            headers=SETTINGS['SIEM_SETTINGS']['SPLUNK_HEADERS'], verify=False)
    data_list = []
    try:
        for item in get_data.json():
            data_list.append(item['value'])
    except:
        pass

    return get_data.status_code, data_list


def splunk_add_to_kv(SETTINGS, ioc_type, element_type, days, update_time, data_list, execution_id):
    kv_name = generate_siem_storage_name(SETTINGS, ioc_type)
    element_type = splunk_get_element_type(SETTINGS, element_type)

    post_status, post_text = '001', 'error in splunk_add_to_kv function'

    if not check_siem_storage_in_db(SETTINGS, ioc_type):
        message = 'mode="AGENT" type="{}" details="Creating KV Store in SPLUNK" ' \
                  'value="{}"'.format(ioc_type, kv_name)
        # print(message)
        logging.info(message)

        post_status, post_text = splunk_create_kv(SETTINGS, kv_name, element_type)

        already_in_use = re.findall(SETTINGS['SIEM_SETTINGS']['SPLUNK_ALREADY_IN_USE'], post_text)

        if check_status_code(post_status) or already_in_use:
            sqlite_command(SETTINGS, SQL_TO_ADD_SIEM_STORAGE_IN_DB, (ioc_type, kv_name, 1, update_time))

            message = 'mode="AGENT" type="{}" details="Created KV Store in SPLUNK" ' \
                      'value="{} - {} - {}"'.format(ioc_type, kv_name, post_status, post_text)
            logging.info(message)
        else:
            message = 'mode="AGENT" type="{}" details="Error while try to create KV Store in SPLUNK" ' \
                      'value="{} - {} - {}"'.format(ioc_type, kv_name, post_status, post_text)
            logging.error(message)
    else:
        post_status, post_text = splunk_load(SETTINGS, kv_name, data_list, ioc_type)

        if check_status_code(post_status):
            sqlite_command(SETTINGS, SQL_TO_UPDATE_LAST_SYNC_SIEM_STORAGE, (update_time, ioc_type))

    check_run_status(SETTINGS, execution_id)

    return post_status, post_text
