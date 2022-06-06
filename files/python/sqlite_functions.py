import datetime
import inspect
import logging
import re
import sqlite3
from files.python.constants import DATE_TIME_FORMAT, SQL_TO_ADD_EXECUTION_HISTORY, \
    SQL_TO_GET_ID_OF_EXECUTION_HISTORY, SQL_TO_GET_DATA_OF_EXECUTION_HISTORY, SQL_TO_UPDATE_EXECUTION_HISTORY, \
    SQL_TO_ADD_CONNECTION_ERROR, SQL_TO_GET_CONNECTION_ERROR, SQL_TO_GET_DATA_CONNECTION_ERROR, \
    SQL_TO_GET_START_EXECUTION
from files.python.error_register import error_register


def sqlite_command(all_settings, sql_query, tuple_list=()):
    try:
        connection = sqlite3.connect(all_settings['DATABASE_FILE'])
        cursor = connection.cursor()

        if tuple_list:
            cursor.execute(sql_query, tuple_list)
        else:
            cursor.execute(sql_query)

        data = cursor.fetchall()
        connection.commit()
        cursor.close()

        return True, data

    except Exception as e:
        message = 'details="Error while connecting to DB" value="{}" sql_query="{}"'.format(sqlite3.Error,
                                                                                            sql_query.encode('ascii', 'ignore').decode('utf-8'))
        logging.error(message)

        error_register(all_settings, str(__name__), str(inspect.stack()[0][3]), e)

        return False, []


def execution_start_register(all_settings, mode):
    now = datetime.datetime.now()
    start_execution = now.strftime(DATE_TIME_FORMAT)

    sqlite_command(all_settings, SQL_TO_ADD_EXECUTION_HISTORY, (mode, start_execution))

    execution_id = sqlite_command(all_settings, SQL_TO_GET_ID_OF_EXECUTION_HISTORY, (mode, start_execution))[1][-1][0]

    message = str(sqlite_command(all_settings, SQL_TO_GET_DATA_OF_EXECUTION_HISTORY, (execution_id, )))
    message = message.replace('"', "'")
    message = 'details="Process started" value="{}"'.format(message.encode('ascii', 'ignore').decode('utf-8'))
    logging.info(message)

    return execution_id


def execution_stop_register(all_settings, execution_id, status):

    start_execution = sqlite_command(all_settings, SQL_TO_GET_START_EXECUTION, (execution_id, ))[1][0][0]

    if type(start_execution) is str:
        start_execution = datetime.datetime.strptime(start_execution, DATE_TIME_FORMAT)

    now = datetime.datetime.now()
    total_time = str(now - start_execution)
    now_str = now.strftime(DATE_TIME_FORMAT)

    status = status.replace('"', '\"')

    sqlite_command(all_settings, SQL_TO_UPDATE_EXECUTION_HISTORY, (now_str, total_time, status, execution_id))

    message = str(sqlite_command(all_settings, SQL_TO_GET_DATA_OF_EXECUTION_HISTORY, (execution_id, )))
    message = message.replace('"', "'")
    message = 'details="Process finished" value="{}"'.format(message.encode('ascii', 'ignore').decode('utf-8'))
    logging.info(message)


def connection_error_register(all_settings, destination, details):
    now = datetime.datetime.now()
    now_str = now.strftime(DATE_TIME_FORMAT)
    sqlite_command(all_settings, SQL_TO_ADD_CONNECTION_ERROR,
                   (destination, now_str, details))

    execution_id = sqlite_command(all_settings, SQL_TO_GET_CONNECTION_ERROR,
                                  (destination, now_str,
                                   details))[1][-1][0]

    message = str(sqlite_command(all_settings, SQL_TO_GET_DATA_CONNECTION_ERROR, (execution_id, )))
    message = message.replace('"', "'")
    message = 'details="Connection error" value="{}"'.format(message.encode('ascii', 'ignore').decode('utf-8'))
    logging.error(message)

    return execution_id, now
