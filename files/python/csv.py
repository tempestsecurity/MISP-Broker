#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import re
import subprocess
import csv
import inspect
import logging
import time
import shutil
import pandas as pd
from files.python.constants import SQL_TO_ADD_SIEM_STORAGE_IN_DB, SQL_TO_UPDATE_LAST_SYNC_SIEM_STORAGE
from files.python.error_register import error_register
from files.python.global_functions import check_status_code, check_siem_storage_in_db, generate_siem_storage_name, check_run_status
from files.python.sqlite_functions import sqlite_command

CSV_FILE = '{}/{}.csv'
CSV_FILE_TMP = '{}/{}.tmp'

def csv_create(all_settings, file_name):
    # Create reference set with default ttl

    file_path=all_settings['SIEM_SETTINGS']['SIEM_ADDRESS']
    csv_file = CSV_FILE.format(file_path, file_name)

    try:
        with open(csv_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['value'])

        return "200", "CSV file {} was created".format(file_name)

    except Exception as e:
        return "500", e


def csv_add(all_settings, file_name, data_list):
    # Loads a list to existing csv file

    file_path=all_settings['SIEM_SETTINGS']['SIEM_ADDRESS']
    data_to_file = []

    for item in data_list:
        data_to_file.append([item])

    if data_to_file:

        shell_file = '{}/{}'.format(file_path, file_name)
        csv_file = '{}.csv'.format(shell_file)
        tmp_csv = '{}.tmp'.format(shell_file)

        try:
            shutil.copyfile(csv_file, tmp_csv)
            with open(tmp_csv, 'a') as f:
                writer = csv.writer(f)
                writer.writerows(data_to_file)

            try:
                shell_query = "cp {}.tmp {}.tmp1 && wc -l {}.tmp1 | cut -d' ' -f1 && sed -i -e 's/\r//g' {}.tmp1 && sed -i '/^value$/d' {}.tmp1 && cat {}.tmp1 | sort -u > {}.tmp2 && mv {}.tmp2 {}.tmp1 && sed -i '/^$/d' {}.tmp1 && sed -i '1i value' {}.tmp1 && mv {}.tmp1 {}.tmp && wc -l {}.tmp".format(shell_file, shell_file, shell_file, shell_file, shell_file, shell_file, shell_file, shell_file, shell_file, shell_file, shell_file, shell_file, shell_file, shell_file)
                execution = str(subprocess.check_output(shell_query, shell=True).decode(encoding='utf-8', errors='strict'))

                message = 'count="1/1" details="Dedup successfully in the {} CSV file" status="{}"'.format(file_name, str(execution.replace('\n', ' ')))
                logging.info(message)

            except Exception as e:
                message = 'count="1/1" details="Dedup ERROR in the {} CSV file" status="{}"'.format(file_name, e)
                logging.error(message)

            shutil.move(tmp_csv, csv_file)

            message = 'count="1/1" details="Saved successfully the {} CSV file" posted="{}" status_code="200"'.format(file_name, str(len(data_to_file)))
            logging.info(message)

            return 200, 'Saved'

        except Exception as e:
            message = 'count="1/1" details="Saved ERROR in the {} CSV file" post_count="{}" status_code="500" status_text="{}" post_data="{}"'.format(file_name, str(len(data_to_file)), e, data_to_file)
            logging.error(message)
            time.sleep(2)
            return "500", e
    else:
        return 200, 'already saved, not to do'


def csv_list_data(all_settings, file_name):

    file_path=all_settings['SIEM_SETTINGS']['SIEM_ADDRESS']
    csv_file = CSV_FILE.format(file_path, file_name)
    data_list = []

    with open(csv_file) as f:
        reader = csv.reader(f)
        data_lists = list(reader)

        for items in data_lists:
            for item in items:
                data_list.append(item)

    return data_list


def csv_purge_csv(all_settings, file_name):

    file_path = all_settings['SIEM_SETTINGS']['SIEM_ADDRESS']
    csv_file = CSV_FILE.format(file_path, file_name)

    message = '{} not exists!'.format(file_name)

    if os.path.exists(csv_file):
        os.remove(csv_file)
        message = '{} deleted!'.format(file_name)

    logging.info(message)

    return 200, message


def csv_delete_item(all_settings, file_name, item):
    # Delete single data

    try:
        file_path=all_settings['SIEM_SETTINGS']['SIEM_ADDRESS']
        csv_file = CSV_FILE.format(file_path, file_name)
        tmp_csv = CSV_FILE_TMP.format(file_path, file_name)

        shutil.copyfile(csv_file, tmp_csv)

        df = pd.read_csv(tmp_csv)
        df = df[df.value != item]

        df.to_csv(tmp_csv, index=False)

        shutil.move(tmp_csv, csv_file)

        return 200, '{} deleted in {}'.format(item, file_name)
    except Exception as e:
        error_register(all_settings, str(__name__), str(inspect.stack()[0][3]), e)
        quit()


def csv_add_to_file(all_settings, ioc_type, update_time, data_list, execution_id):
    file_name = generate_siem_storage_name(all_settings, ioc_type)

    post_status, post_text = '001', 'error in csv_add_to_file function'

    if not check_siem_storage_in_db(all_settings, ioc_type):
        message = 'mode="AGENT" type="{}" details="Creating CSV file" ' \
                  'value="{}"'.format(ioc_type, file_name)

        logging.info(message)

        post_status, post_text = csv_create(all_settings, file_name)

        if check_status_code(post_status):
            sqlite_command(all_settings, SQL_TO_ADD_SIEM_STORAGE_IN_DB, (ioc_type, file_name, 1, update_time))

            message = 'mode="AGENT" type="{}" details="Created CSV File" ' \
                      'value="{} - {} - {}"'.format(ioc_type, file_name, post_status, post_text)
            logging.info(message)
        else:
            message = 'mode="AGENT" type="{}" details="Error while try to create CSV File" ' \
                      'value="{} - {} - {}"'.format(ioc_type, file_name, post_status, post_text)
            logging.error(message)
    else:
        post_status, post_text = csv_add(all_settings, file_name, data_list)

        if check_status_code(post_status):
            sqlite_command(all_settings, SQL_TO_UPDATE_LAST_SYNC_SIEM_STORAGE, (update_time, ioc_type))

    check_run_status(all_settings, execution_id)

    return post_status, post_text
