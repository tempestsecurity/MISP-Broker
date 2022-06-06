#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import logging
import os
import re
import shutil
import sys
import getpass
import configparser
from time import sleep
from files.python.constants import BROKER_SETTINGS, SIEM_LIST, SIEM_HELP, LOG_MODE, LOG_OUTPUT_FORMAT, CODENAME_HELP, RUNNING_FILE_CONTENT, DATABASE_INITIALIZER_agent_iocs, DATABASE_INITIALIZER_agent_last_sync, DATABASE_INITIALIZER_execution_history, DATABASE_INITIALIZER_connection_errors, DATABASE_INITIALIZER_agent_siem_storage, DATABASE_INITIALIZER_lived_days_update_history, DATABASE_INITIALIZER_exceptions, SQL_TO_SHOW_VERSION, BROKER_SETTING_FILE
from files.python.global_functions import check_run_status
from files.python.sqlite_functions import sqlite_command
from files.python.agent import agent


# Driver Code
if __name__ == "__main__":

    print('Running')

    events_count_by_type = {}
    api_return_format = 'application/json'

    START_FILE = True
    can_use_logging = False
    LOGGING_SETTINGS = {'DEBUG': 'True'}

    while True:

        # Defining MISP Broker Settings

        if can_use_logging:
            message = 'details="Reloading Broker settings" value="{}" loglevel={}'.format(BROKER_SETTING_FILE, BROKER_SETTINGS['LOG_LEVEL'])
            print('Loading Broker settings: {}'.format(BROKER_SETTING_FILE))
            logging.info(message)
        else:
            print('Loading Broker settings: {}'.format(BROKER_SETTING_FILE))

        try:
            settings_parser = configparser.RawConfigParser(inline_comment_prefixes="#")
            settings_parser.optionxform = lambda option: option
            settings_parser.read(BROKER_SETTING_FILE)
            BROKER_SETTINGS = dict(settings_parser.items('BROKER_SETTINGS'))
            BROKER_SETTINGS['WAIT_TIME'] = int(BROKER_SETTINGS['WAIT_TIME'])
            BROKER_SETTINGS['INTERVAL_TIME'] = int(BROKER_SETTINGS['INTERVAL_TIME'])
            BROKER_SETTINGS['PERCENT_STEP_LOG'] = int(BROKER_SETTINGS['PERCENT_STEP_LOG'])
            BROKER_SETTINGS['DEFAULT_TTL'] = int(BROKER_SETTINGS['DEFAULT_TTL'])
            BROKER_SETTINGS['RANGE_TIME'] = int(BROKER_SETTINGS['RANGE_TIME'])
            BROKER_SETTINGS['UPDATE_LOOKBACK'] = int(BROKER_SETTINGS['UPDATE_LOOKBACK'])

        except Exception as e:
            if can_use_logging:
                message = 'details="Error when try to load settings" value="{} - {}"'.format(BROKER_SETTING_FILE, e)
                print('Error when try to load settings: {}\n{}'.format(BROKER_SETTING_FILE, e))
                logging.error(message)
            else:
                print('Error when try to load settings: {}\n{}'.format(BROKER_SETTING_FILE, e))

            quit()

        # Define config file variables

        config_file = ''
        SIEM = ''

        try:
            config_file = sys.argv[1].split('.')[0]
        except Exception as e:
            if can_use_logging:
                message = 'details="You need to give one cfg file!" value="{}"'.format(e)
                print('You need to give one cfg file!\n{}'.format(e))
                logging.error(message)
            else:
                print('You need to give one cfg file!\n{}'.format(e))

            quit()

        if config_file == '':
            if can_use_logging:
                message = 'details="You need to give one cfg file!" value="null"'
                print('You need to give one cfg file!')
                logging.error(message)
            else:
                print('You need to give one cfg file!')

            quit()

        LOG_FILE = 'logs/{}.log'.format(config_file)

        if config_file == 'default':
            if can_use_logging:
                message = 'details="You need to give one valid cfg file, default is only to copy and create a new cfg!" value="default"'
                print('You need to give one valid cfg file, default is only to copy and create a new cfg!')
                logging.error(message)
            else:
                print('You need to give one valid cfg file, default is only to copy and create a new cfg!')

            quit()

        if can_use_logging:
            message = 'details="Reloading config" value="./configs/{}.cfg"'.format(config_file)
            print('Loading config: configs/{}.cfg'.format(config_file))
            logging.info(message)
        else:
            print('Loading config: configs/{}.cfg'.format(config_file))

        try:
            config_parser = configparser.RawConfigParser(inline_comment_prefixes="#")
            config_parser.optionxform = lambda option: option
            config_parser.read('./configs/{}.cfg'.format(config_file))

            # Logging Settings
            try:
                LOGGING_SETTINGS = dict(config_parser.items('LOGGING_SETTINGS'))
            except Exception:
                pass

            logging.basicConfig(
                level=logging.DEBUG,
                filename=LOG_FILE,
                filemode=LOG_MODE,
                format=LOG_OUTPUT_FORMAT,
            )

            if LOGGING_SETTINGS['DEBUG'].lower() == 'false':
                logging.getLogger('root').setLevel(level=logging.INFO)

            can_use_logging = True

            # MISP Settings
            MISP_SETTINGS = dict(config_parser.items('MISP_SETTINGS'))
            MISP_SETTINGS['MISP_API_URL'] = "{}://{}/attributes/restSearch".format(MISP_SETTINGS['MISP_PROTOCOL'], MISP_SETTINGS['MISP_ADDRESS'])
            MISP_SETTINGS['SIGHTINGS_URL'] = "{}://{}/sightings/index/".format(MISP_SETTINGS['MISP_PROTOCOL'], MISP_SETTINGS['MISP_ADDRESS'])
            MISP_SETTINGS['SIGHTINGS_RECENT_URL'] = "{}://{}/sightings/restSearch/".format(MISP_SETTINGS['MISP_PROTOCOL'], MISP_SETTINGS['MISP_ADDRESS'])
            MISP_SETTINGS['MISP_HEADERS'] = {
                'Authorization': MISP_SETTINGS['MISP_API_TOKEN'],
                'Accept': api_return_format,
                'Content-Type': api_return_format,
            }
            MISP_SETTINGS['MISP_BODY_BY_TYPE'] = {
                "returnFormat": "json",

                "type": {
                    "AND": []
                },
            }
            MISP_SETTINGS['MISP_BODY_SIGHTINGS'] = {
                "returnFormat": "json",
            }
            MISP_SETTINGS['MISP_BODY_LAST_UPDATES'] = {
                "returnFormat": "json",
            }

            try:
                if MISP_SETTINGS['MISP_VERIFY_SSL'].lower() == 'false':
                    MISP_SETTINGS['MISP_VERIFY_SSL'] = False
                else:
                    MISP_SETTINGS['MISP_VERIFY_SSL'] = True
            except Exception:
                MISP_SETTINGS['MISP_VERIFY_SSL'] = True

            # SIEM Settings
            SIEM_SETTINGS = dict(config_parser.items('SIEM_SETTINGS'))
            SIEM_SETTINGS['SIEM'] = SIEM_SETTINGS['SIEM'].upper()

            try:
                if SIEM_SETTINGS['SIEM_VERIFY_SSL'].lower() == 'false':
                    SIEM_SETTINGS['SIEM_VERIFY_SSL'] = False
                else:
                    SIEM_SETTINGS['SIEM_VERIFY_SSL'] = True
            except Exception:
                SIEM_SETTINGS['SIEM_VERIFY_SSL'] = True

            if SIEM_SETTINGS['SIEM'] == 'QRADAR':
                # QRadar Settings
                SIEM_SETTINGS['QRADAR_ALREADY_IN_USE'] = 'the name provided is already in use'
                SIEM_SETTINGS['QRADAR_BULK_URL'] = '{}://{}:{}/api/reference_data/sets/bulk_load/'.format(SIEM_SETTINGS['SIEM_PROTOCOL'], SIEM_SETTINGS['SIEM_ADDRESS'], SIEM_SETTINGS['SIEM_PORT'])
                SIEM_SETTINGS['QRADAR_SIEM_STORAGE_URL'] = '{}://{}:{}/api/reference_data/sets/'.format(SIEM_SETTINGS['SIEM_PROTOCOL'], SIEM_SETTINGS['SIEM_ADDRESS'], SIEM_SETTINGS['SIEM_PORT'])
                SIEM_SETTINGS['QRADAR_REFERENCE_DATA_URL'] = '{}://{}:{}/api/reference_data/sets?'.format(SIEM_SETTINGS['SIEM_PROTOCOL'], SIEM_SETTINGS['SIEM_ADDRESS'], SIEM_SETTINGS['SIEM_PORT'])
                SIEM_SETTINGS['QRADAR_REFERENCE_DATA_LIST_ITEM_URL'] = '{}://{}:{}/api/reference_data/sets/'.format(SIEM_SETTINGS['SIEM_PROTOCOL'], SIEM_SETTINGS['SIEM_ADDRESS'], SIEM_SETTINGS['SIEM_PORT'])
                SIEM_SETTINGS['QRADAR_HEADERS'] = {
                    'SEC': SIEM_SETTINGS['SIEM_API_TOKEN'],
                    'Version': SIEM_SETTINGS['SIEM_API_VERSION'],
                    'Accept': api_return_format,
                    'Accept-Encoding': 'identity',
                }

            elif SIEM_SETTINGS['SIEM'] == 'SPLUNK':
                # Splunk Settings
                SIEM_SETTINGS['APP_DIR'] = 'a1_splunk_misp'
                SIEM_SETTINGS['APP_FILE'] = '{}/default/app.conf'.format(SIEM_SETTINGS['APP_DIR'])
                SIEM_SETTINGS['COLLECTIONS_FILE'] = '{}/default/collections.conf'.format(SIEM_SETTINGS['APP_DIR'])
                SIEM_SETTINGS['TRANSFORMS_FILE'] = '{}/default/transforms.conf'.format(SIEM_SETTINGS['APP_DIR'])
                SIEM_SETTINGS['LIMITS_FILE'] = '{}/default/limits.conf'.format(SIEM_SETTINGS['APP_DIR'])
                SIEM_SETTINGS['META_FILE'] = '{}/metadata/default.meta'.format(SIEM_SETTINGS['APP_DIR'])
                SIEM_SETTINGS['SPLUNK_SEARCH_URL'] = '{}://{}:{}/services/search/jobs/export'.format(SIEM_SETTINGS['SIEM_PROTOCOL'], SIEM_SETTINGS['SIEM_ADDRESS'], SIEM_SETTINGS['SIEM_PORT'])
                SIEM_SETTINGS['SPLUNK_KV_CONFIG_URL'] = '{}://{}:{}/servicesNS/nobody/{}/storage/collections/config'.format(SIEM_SETTINGS['SIEM_PROTOCOL'], SIEM_SETTINGS['SIEM_ADDRESS'], SIEM_SETTINGS['SIEM_PORT'], SIEM_SETTINGS['APP_DIR'])
                SIEM_SETTINGS['SPLUNK_KV_DATA_URL'] = '{}://{}:{}/servicesNS/nobody/{}/storage/collections/data/{}'.format(SIEM_SETTINGS['SIEM_PROTOCOL'], SIEM_SETTINGS['SIEM_ADDRESS'], SIEM_SETTINGS['SIEM_PORT'], SIEM_SETTINGS['APP_DIR'], '{}')
                SIEM_SETTINGS['SPLUNK_KV_BATCH_URL'] = '{}://{}:{}/servicesNS/nobody/{}/storage/collections/data/{}/batch_save'.format(SIEM_SETTINGS['SIEM_PROTOCOL'], SIEM_SETTINGS['SIEM_ADDRESS'], SIEM_SETTINGS['SIEM_PORT'], SIEM_SETTINGS['APP_DIR'], '{}')
                SIEM_SETTINGS['SPLUNK_HEADERS'] = {
                    'Authorization': 'Bearer {}'.format(SIEM_SETTINGS['SIEM_API_TOKEN']),
                    'Accept': api_return_format,
                    'Content-Type': api_return_format
                }
                SIEM_SETTINGS['APP_CONF'] = '[install]\n' \
                           'build = 0\n' \
                           '\n' \
                           '[ui]\n' \
                           'is_visible = 0\n' \
                           'label = Tempest MISP\n' \
                           '\n' \
                           '[launcher]\n' \
                           'author = .\n' \
                           'description = .\n' \
                           'version = {}\n' \
                           '\n' \
                           '[package]\n' \
                           'id = a1_splunk_misp\n' \
                           '\n'.format(SIEM_SETTINGS['SIEM_APP_VERSION'])
                SIEM_SETTINGS['DEFAULT_META'] = '[]\n' \
                               'export = system\n'
                SIEM_SETTINGS['SPLUNK_ELEMENT_TYPE_STRING'] = ['ALN', 'ALNIC', ]
                SIEM_SETTINGS['SPLUNK_ELEMENT_TYPE_CIDR'] = ['IP']
                SIEM_SETTINGS['SPLUNK_ELEMENT_TYPE_NUMBER'] = ['NUM']
                SIEM_SETTINGS['SPLUNK_OUTPUT_MODE'] = {'output_mode': 'json'}
                SIEM_SETTINGS['SPLUNK_ALREADY_IN_USE'] = 'already exists'
                SIEM_SETTINGS['SPLUNK_QUERY_SEARCH_IOC'] = '| inputlookup {} where value = {} | rename _key as view_key'
                SIEM_SETTINGS['SPLUNK_DEDUP_SEARCH'] = '| inputlookup {} | dedup value | outputlookup {}'

            elif SIEM_SETTINGS['SIEM'] == 'CSV':
                # CSV Settings
                SIEM_SETTINGS['SIEM_ADDRESS'] = re.sub(r'/$', '', SIEM_SETTINGS['SIEM_ADDRESS'])
                SIEM_SETTINGS['SIEM_ADDRESS'] = '{}/{}'.format(SIEM_SETTINGS['SIEM_ADDRESS'], config_file)
                SIEM_SETTINGS['CSV_ALREADY_IN_USE'] = 'File exists'

                try:
                    os.mkdir(SIEM_SETTINGS['SIEM_ADDRESS'])
                except Exception as e:
                    if SIEM_SETTINGS['CSV_ALREADY_IN_USE'] not in str(e):
                        message = 'details="Error when try to load config" value="./configs/{}.cfg - {}'.format(config_file, e)
                        logging.error(message)
                        quit()

        except Exception as e:
            if can_use_logging:
                message = 'details="Error when try to load config" value="./configs/{}.cfg - {}'.format(config_file, e)
                logging.error(message)
                print('Error when try to load config" value="./configs/{}.cfg - {}'.format(config_file, e))
            else:
                print('Error when try to load config" value="./configs/{}.cfg - {}'.format(config_file, e))
            quit()

        if SIEM_SETTINGS['SIEM'] not in SIEM_LIST:
            print(SIEM_HELP.format(SIEM_SETTINGS['SIEM']))
            logging.warning(SIEM_HELP.format(SIEM_SETTINGS['SIEM']))
            quit()

        DATABASE_FILE = 'files/databases/{}.db'.format(config_file)

        # Check user

        if getpass.getuser() == 'root':
            message = 'root user is not allowed, run with common user!'
            logging.error(message)
            print(message)
            quit()

        try:
            message = 'details="Initializing MISP Broker" value="{}"'.format(config_file)
            print('Initializing MISP Broker: {}'.format(config_file))
            logging.info(message)
        except Exception:
            logging.error((CODENAME_HELP.format(config_file, 'joya')))
            print(CODENAME_HELP.format(config_file, 'joya'))
            quit()

        # Settings Var

        SETTINGS = {
            'BROKER_SETTINGS': BROKER_SETTINGS,
            'LOGGING_SETTINGS': LOGGING_SETTINGS,
            'MISP_SETTINGS': MISP_SETTINGS,
            'SIEM_SETTINGS': SIEM_SETTINGS,
            'DATABASE_FILE': DATABASE_FILE,
            'RUNNING_FILE': 'runnings/{}.std'.format(config_file)
        }

        # Create running broker register

        if START_FILE:
            with open(SETTINGS['RUNNING_FILE'], 'w') as fp:
                fp.write(RUNNING_FILE_CONTENT.format(datetime.datetime.now()))
            START_FILE = False

        # Config database manager

        message = 'details="SQLite Database Version" value="{}"'.format(sqlite_command(SETTINGS, SQL_TO_SHOW_VERSION)[1][0][0])
        logging.info(message)

        database_info = sqlite_command(SETTINGS, 'select * from agent_iocs;')

        if not database_info[0] and len(database_info[1]) == 0:
            message = 'Database created and Successfully Connected to SQLite {}'.format(DATABASE_FILE)
            logging.info(message)
            print(message)
            sqlite_command(SETTINGS, DATABASE_INITIALIZER_agent_iocs)
            sqlite_command(SETTINGS, DATABASE_INITIALIZER_agent_last_sync)
            sqlite_command(SETTINGS, DATABASE_INITIALIZER_execution_history)
            sqlite_command(SETTINGS, DATABASE_INITIALIZER_connection_errors)
            sqlite_command(SETTINGS, DATABASE_INITIALIZER_agent_siem_storage)
            sqlite_command(SETTINGS, DATABASE_INITIALIZER_lived_days_update_history)
            sqlite_command(SETTINGS, DATABASE_INITIALIZER_exceptions)

        # Broker Start

        message = "Let's GO!!! ({} - {} - {} - {})".format('configs/{}.cfg'.format(config_file), DATABASE_FILE, SETTINGS['RUNNING_FILE'], LOG_FILE)
        logging.info(message)
        print(message)

        events_count_by_type = agent(SETTINGS, events_count_by_type)

        message = "Finish!!! ({} - {} - {} - {})".format('configs/{}.cfg'.format(config_file), DATABASE_FILE, SETTINGS['RUNNING_FILE'], LOG_FILE)
        logging.info(message)
        print(message)

        # Broker check stop requests

        check_run_status(SETTINGS)

        # Wait to restart...

        sleep(BROKER_SETTINGS['INTERVAL_TIME'])
