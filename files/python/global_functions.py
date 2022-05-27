import datetime
import logging
import re
import socket

from files.python.constants import TYPE_LIST, TYPE_LIST_HELP, TYPE_LIST_SAMPLE, REGEX_IPV4, DATE_FORMAT, \
    SQL_TO_CHECK_SIEM_STORAGE_IN_DB
from files.python.sqlite_functions import execution_stop_register, sqlite_command


def check_run_status(SETTINGS, execution_id=None):
    try:
        with open(SETTINGS['RUNNING_FILE'], 'r') as fp:
            pass
    except:
        message = 'details="{} not found, stopping service now"'.format(SETTINGS['RUNNING_FILE'])
        logging.warning(message)

        if execution_id is not None:
            execution_stop_register(SETTINGS, execution_id, message)
        quit()


def get_type_and_feed_lists(SETTINGS, execution_id):
    """ Function to return the lists of types and custom feeds based on files type_list.txt and custom_feed.txt """

    type_list = {}
    tl_file = TYPE_LIST

    try:
        if SETTINGS['MISP_SETTINGS']['MISP_TYPE_LIST']:
            tl_file = 'type_list-{}.txt'.format(SETTINGS['MISP_SETTINGS']['MISP_TYPE_LIST'])
    except:
        pass

    try:
        with open(tl_file, 'r') as l:
            for t in l:
                line = re.sub(r'\n', '', t)
                if not re.findall(r'^#', line):
                    type_list[line.split()[0]] = {}
                    type_list[line.split()[0]]['ttl'] = line.split()[1]
                    type_list[line.split()[0]]['element_type'] = line.split()[2]
    except:
        logging.warning(TYPE_LIST_HELP)
        print(TYPE_LIST_HELP)
        with open(tl_file, 'w') as f:
            f.write(TYPE_LIST_SAMPLE)
        execution_stop_register(SETTINGS, execution_id, TYPE_LIST_HELP)
        return [], []

    custom_feed = []

    return type_list, custom_feed


def progress_logging(SETTINGS, total, actual):
    total = int(total)
    start_percent = 0
    progress_count = 1
    percent_step = 100 / SETTINGS['BROKER_SETTINGS']['PERCENT_STEP_LOG']
    step = int(total / percent_step)
    logging_list = []

    while start_percent <= 100:
        logging_list.append(int(progress_count))

        start_percent += SETTINGS['BROKER_SETTINGS']['PERCENT_STEP_LOG']
        progress_count += step

    logging_list.pop(-1)
    logging_list.append(int(total))

    if actual in logging_list:

        # Open bar
        bar = '['

        # Create filled bar
        actual_percent = logging_list.index(actual)

        if actual == total:
            actual_percent = 100
        elif actual == 1:
            actual_percent = 1
        else:
            actual_percent = actual_percent * SETTINGS['BROKER_SETTINGS']['PERCENT_STEP_LOG']

        bar_count = 0

        while bar_count < actual_percent:
            bar = '{}#'.format(bar)
            bar_count += 1

        # Create empty bar
        bar_count = 1

        diff_percent = 100 - actual_percent

        while bar_count <= diff_percent:
            bar = '{}='.format(bar)
            bar_count += 1

        # Close bar
        bar = '{}] {}%'.format(bar, str(actual_percent).zfill(3))

        return bar

    else:
        return None


def check_status_code(status_code, intended=2):
    regex = '{}[0-9]{{2}}'.format(str(intended))
    find = re.findall(regex, str(status_code))

    if find:
        return True
    else:
        return False


def calc_lived_days(date_only, ioc_lived_days):
    if type(date_only) == str:
        date_only = datetime.datetime.strptime(date_only, DATE_FORMAT)

    now = datetime.datetime.now()

    diff_days = (now - date_only).days
    new = ioc_lived_days + diff_days

    return int(new)


def is_exception(SETTINGS, ioc, sightings_list):
    comment = False
    if SETTINGS['BROKER_SETTINGS']['MISP_COMMENT_EXCEPTION'] != '':
        comment = re.findall(SETTINGS['BROKER_SETTINGS']['MISP_COMMENT_EXCEPTION'].lower(), str(ioc['comment']).lower())

    tags = False
    if SETTINGS['BROKER_SETTINGS']['MISP_TAG_EXCEPTION'] != '':
        try:
            for tag in ioc['Tag']:
                if re.findall(SETTINGS['BROKER_SETTINGS']['MISP_TAG_EXCEPTION'], str(tag['name']).lower()):
                    tags = True
        except:
            pass

    sightings_found = {}

    for sighting in sightings_list:
        if sighting['attribute_id'] == ioc['id']:
            sightings_found[sighting['uuid']] = {"date_sighting": sighting['date_sighting'], "type": sighting['type']}

    sightings_last = {'date': 0, 'type': 0}
    for uuid in sightings_found:
        if int(sightings_found[uuid]['date_sighting']) > int(sightings_last['date']):
            sightings_last = {'date': sightings_found[uuid]['date_sighting'], 'type': sightings_found[uuid]['type']}

    if comment or tags or sightings_last['type'] == '1' or str(ioc['to_ids']).lower() == 'false' or str(
            ioc['deleted']).lower() == 'true':
        return True, int(sightings_last['date'])
    else:
        return False, int(sightings_last['date'])


def is_ipv4(ip):
    if re.findall(REGEX_IPV4, ip):
        return True
    else:
        return False


def is_ipv6(ip):
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except socket.error:
        return False


def is_ioc_ip_and_port(ip_port):
    if re.findall(r'|', ip_port):
        return True
    else:
        return False


def is_type_ip_and_port(ioc_type):
    if re.findall(r'port', ioc_type):
        return True
    else:
        return False


def is_dual_value(ioc_type, value):
    if re.findall(r'\|', ioc_type):
        ioc_type = True
    else:
        ioc_type = False

    if re.findall(r'\|', value):
        value = True
    else:
        value = False

    return [ioc_type, value]


def maybe_a_file(filename):
    if re.findall(r'\.', filename):
        return True
    else:
        return False


def check_siem_storage_in_db(SETTINGS, ioc_type):
    last_sync = sqlite_command(SETTINGS, SQL_TO_CHECK_SIEM_STORAGE_IN_DB, (ioc_type,))
    last_sync = len(last_sync[1])

    if last_sync == 0:
        return False
    else:
        return True


def generate_siem_storage_name(SETTINGS, ioc_type=None):

    if ioc_type is not None:
        if SETTINGS['SIEM_SETTINGS']['SIEM'].upper() == 'SPLUNK' or SETTINGS['SIEM_SETTINGS']['SIEM'].upper() == 'CSV':
            siem_storage_name = str(re.sub(r'\|', '_', ioc_type))
        else:
            siem_storage_name = str(ioc_type)

        if re.findall('misp_', siem_storage_name):
            return siem_storage_name

    else:
        siem_storage_name = ''

    siem_storage_name = 'tsi_misp_{}'.format(siem_storage_name)

    return siem_storage_name
