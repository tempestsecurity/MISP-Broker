#!/usr/bin/python3
# -*- coding: utf-8 -*-
import inspect
import logging
import re
import urllib
import requests
import time

from urllib3 import disable_warnings
from json import dumps

from files.python.constants import SQL_TO_ADD_SIEM_STORAGE_IN_DB, SQL_TO_UPDATE_LAST_SYNC_SIEM_STORAGE
from files.python.error_register import error_register
from files.python.global_functions import check_status_code, check_siem_storage_in_db, generate_siem_storage_name, check_run_status
from files.python.sqlite_functions import sqlite_command


disable_warnings()


def generate_qradar_ttl(ttl):

    ttl = int(ttl)
    ttl += 10

    years = int(ttl/365)
    ttl = int(ttl%365)
    months = int(ttl/31)
    days = int(ttl%31)
    if days == 30:
        days -= 1

    ttl_str = ''

    if years > 0:
        ttl_str = '{}%20years'.format(years)

    if months > 0:
        if ttl_str == '':
            ttl_str = '{}%20months'.format(months)
        else:
            ttl_str = '{}%20{}%20months'.format(ttl_str, months)

    if days > 0:
        if ttl_str == '':
            ttl_str = '{}%20days'.format(days)
        else:
            ttl_str = '{}%20{}%20days'.format(ttl_str, days)

    return ttl_str


def qradar_create_refence_set(SETTINGS, element_type, reference_set_name, ttl):
    # Create reference set with default ttl
    """"Element type. Ex: ALN, NUM, IP, PORT, ALNIC, DATE"""

    if ttl == 0 or ttl == 360000:
        url = '{}element_type={}&name={}&' \
              'timeout_type=LAST_SEEN'.format(SETTINGS['SIEM_SETTINGS']['QRADAR_REFERENCE_DATA_URL'], element_type, reference_set_name)

    else:
        url = '{}element_type={}&name={}&' \
              'timeout_type=LAST_SEEN&time_to_live={}'.format(SETTINGS['SIEM_SETTINGS']['QRADAR_REFERENCE_DATA_URL'], element_type, reference_set_name, generate_qradar_ttl(ttl))

    post_data = requests.post(url, headers=SETTINGS['SIEM_SETTINGS']['QRADAR_HEADERS'], verify=False)

    return post_data.status_code, post_data.text


def qradar_load(SETTINGS, reference_set_name, data_list):
    # Loads a list to existing reference set
    max_amount = 10000
    if SETTINGS['SIEM_SETTINGS']['BATCH_LIST_SIZE'] != '':
        try:
            max_amount = int(SETTINGS['SIEM_SETTINGS']['BATCH_LIST_SIZE'])
        except:
            max_amount = 10000
    count = 0
    split_data_list = []

    status_code = 200
    data_text = 'already synced, not to do'


    for index in range(0, len(data_list), max_amount):
        split_data_list.append(data_list[index: index + max_amount])

    for splitter_list in split_data_list:
        count += 1
        
        url = '{}{}?&namespace=SHARED'.format(SETTINGS['SIEM_SETTINGS']['QRADAR_BULK_URL'], reference_set_name)
        post_data = requests.post(url, data=dumps(splitter_list), headers=SETTINGS['SIEM_SETTINGS']['QRADAR_HEADERS'], verify=False)

        status_code = post_data.status_code
        data_text = post_data.text
        
        if check_status_code(post_data.status_code):
            message = 'count="{}/{}" details="Post successfully the {} batch list to QRADAR" posted="{}" status_code="{}"'.format(count, str(len(split_data_list)), reference_set_name, str(len(splitter_list)), status_code)
            logging.info(message)
            if len(split_data_list) > 1:
                time.sleep(2)
        else:
            message = 'count="{}/{}" details="Post ERROR in the {} batch list to QRADAR" post_count="{}" status_code="{}" status_text="{}" post_data="{}"'.format(count, str(len(split_data_list)), reference_set_name, str(len(splitter_list)), status_code, data_text, dumps(splitter_list))
            logging.error(message)
            time.sleep(2)
            return status_code, data_text
    
    return status_code, data_text


def qradar_list_data(SETTINGS, reference_set_name):

    url = '{}{}'.format(SETTINGS['SIEM_SETTINGS']['QRADAR_REFERENCE_DATA_LIST_ITEM_URL'], reference_set_name)
    json_data = requests.get(url, headers=SETTINGS['SIEM_SETTINGS']['QRADAR_HEADERS'], verify=False).json()

    return json_data


def qradar_purge_reference_set(SETTINGS, reference_set_name):

    url = '{}{}?purge_only=true'.format(SETTINGS['SIEM_SETTINGS']['QRADAR_SIEM_STORAGE_URL'], reference_set_name)
    post_data = requests.delete(url, headers=SETTINGS['SIEM_SETTINGS']['QRADAR_HEADERS'], verify=False)

    return post_data.status_code, post_data.text


def qradar_delete_item(SETTINGS, reference_set_name, item):
    # Delete single data
    item = urllib.parse.quote(item)
    item = urllib.parse.quote(item)
    url = '{}{}/{}'.format(SETTINGS['SIEM_SETTINGS']['QRADAR_SIEM_STORAGE_URL'], reference_set_name, item)

    try:
        delete_data = requests.delete(url, headers=SETTINGS['SIEM_SETTINGS']['QRADAR_HEADERS'], verify=False)

        return delete_data.status_code, delete_data.text
    except Exception as e:
        error_register(SETTINGS, str(__name__), str(inspect.stack()[0][3]), e)
        quit()


def qradar_add_to_reference_set(SETTINGS, ioc_type, element_type, days, update_time, data_list, execution_id):
    reference_set = generate_siem_storage_name(SETTINGS, ioc_type)

    post_status, post_text = '001', 'error in qradar_add_to_reference_set function'

    if not check_siem_storage_in_db(SETTINGS, ioc_type):
        message = 'mode="AGENT" type="{}" details="Creating reference set in QRADAR" ' \
                  'value="{}"'.format(ioc_type, reference_set)

        logging.info(message)

        post_status, post_text = qradar_create_refence_set(SETTINGS, element_type, reference_set, days)

        already_in_use = re.findall(SETTINGS['SIEM_SETTINGS']['QRADAR_ALREADY_IN_USE'], post_text)

        if check_status_code(post_status) or already_in_use:
            sqlite_command(SETTINGS, SQL_TO_ADD_SIEM_STORAGE_IN_DB, (ioc_type, reference_set, 1, update_time))

            message = 'mode="AGENT" type="{}" details="Created reference set in QRADAR" ' \
                      'value="{} - {} - {}"'.format(ioc_type, reference_set, post_status, post_text)
            logging.info(message)
        else:
            message = 'mode="AGENT" type="{}" details="Error while try to create reference set in QRADAR" ' \
                  'value="{} - {} - {}"'.format(ioc_type, reference_set, post_status, post_text)
            logging.error(message)
    else:
        post_status, post_text = qradar_load(SETTINGS, reference_set, data_list)

        if check_status_code(post_status):
            sqlite_command(SETTINGS, SQL_TO_UPDATE_LAST_SYNC_SIEM_STORAGE, (update_time, ioc_type))

    check_run_status(SETTINGS, execution_id)

    return post_status, post_text
