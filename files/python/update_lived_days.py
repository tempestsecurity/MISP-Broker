import datetime
import logging
import re

from files.python.constants import DATE_TIME_FORMAT, DATE_FORMAT, SQL_TO_LIST_LIVED_DAYS_UPDATE, \
    SQL_TO_LIST_ALL_DATE_GROUPS, SQL_TO_UPDATE_LIVED_DAYS_OF_IOCS, SQL_TO_ADD_LIVED_DAYS_HISTORY
from files.python.global_functions import progress_logging, calc_lived_days
from files.python.sqlite_functions import sqlite_command


def update_lived_days(SETTINGS, mode):
    now = datetime.datetime.now()
    now_date_format = datetime.datetime.strftime(now, DATE_FORMAT)
    now_date_time_format = datetime.datetime.strftime(now, DATE_TIME_FORMAT)

    all_executions = sqlite_command(SETTINGS, SQL_TO_LIST_LIVED_DAYS_UPDATE)[1]
    today = False

    for execution in all_executions:
        timestamp = datetime.datetime.strptime(execution[0], DATE_TIME_FORMAT)
        timestamp = datetime.datetime.strftime(timestamp, DATE_FORMAT)
        if timestamp == now_date_format:
            today = True

            break

    if not today:

        all_date_times = sqlite_command(SETTINGS, SQL_TO_LIST_ALL_DATE_GROUPS)[1]
        date_dict = {}

        for date_time in all_date_times:
            date_only = re.sub(r' .*', '', date_time[0])
            date_dict[date_only] = []

        total = 0
        for date_time in all_date_times:
            date_only = re.sub(r' .*', '', date_time[0])
            if date_time[1] not in date_dict[date_only]:
                date_dict[date_only].append(date_time[1])
                total += 1

        message = 'mode="{}" details="Running update lived days of ' \
                  'IOCs" value="{}"'.format(mode, str(len(date_dict)))
        logging.info(message)

        count = 0

        # print(date_dict)
        for date_only in date_dict:
            # print('date_only: {} - {}'.format(date_only, len(date_dict[date_only])))

            for ioc_lived_days in date_dict[date_only]:
                # print('ioc_lived_days: {}'.format(ioc_lived_days))

                new = calc_lived_days(date_only, ioc_lived_days)

                message = 'mode="{}" details="Updating lived day" ' \
                          'value="current:{}, total:{}, date:{}, ' \
                          'before:{}, after:{}"'.format(mode, count, total, date_only, ioc_lived_days, new)
                # print(message)
                logging.debug(message)

                date_only = '{} %'.format(date_only)
                sqlite_command(SETTINGS, SQL_TO_UPDATE_LIVED_DAYS_OF_IOCS, (new, date_only, ioc_lived_days))

                count += 1
                progress = progress_logging(SETTINGS, total, count)

                if progress is not None:
                    message = 'mode="{}" details="Updating lived day of IOCs" ' \
                              'value="{} ({}/{})"'.format(mode, progress, count, total)
                    logging.info(message)

        message = 'mode="{}" details="Checked lived days of {} IOCs" ' \
                  'value="{}"'.format(mode, total, count)
        logging.info(message)

        sqlite_command(SETTINGS, SQL_TO_ADD_LIVED_DAYS_HISTORY, (now_date_time_format, ))
