import datetime
import inspect
import logging
import re
import sqlite3
import traceback
from files.python.constants import DATE_TIME_FORMAT, SQL_TO_ADD_EXCEPTION


def error_register(all_settings, module, function, exception):

    # Remove memory reference to be able to group errors
    traceback_decoded = str(re.sub("object at [0-9a-zA-Z]+>", 'object>', str(traceback.format_exc())))
    exception = str(re.sub("object at [0-9a-zA-Z]+>", 'object>', str(exception)))

    # Check for connection error
    text1 = re.search('(timed out|timeout|unreachable)', exception)
    try:
        text1 = str(text1.group())
    except Exception:
        pass

    # Check for host in error
    text2 = re.search("host='[a-zA-Z0-9:/_.-]+', port=[0-9]+", exception)
    try:
        text2 = str(text2.group())
    except Exception:
        text2 = 'localhost'

    message = 'module="{}" excepted_function="{}" exception="{}" traceback="{}" host="{}"'.format(module,
                                                                                                  function, exception,
                                                                                                  traceback_decoded,
                                                                                                  text2)

    logging.error(message)

    details = 'module="{}"\n\n' \
              'excepted_function="{}"\n\n' \
              'exception="{}"\n\n' \
              'traceback="{}"\n\n' \
              'host="{}"'.format(module, function, exception, traceback_decoded, text2)

    now = datetime.datetime.now()
    now = now.strftime(DATE_TIME_FORMAT)

    try:
        connection = sqlite3.connect(all_settings['DATABASE_FILE'])
        cursor = connection.cursor()
        cursor.execute(SQL_TO_ADD_EXCEPTION, (now, details))
        data = cursor.fetchall()
        connection.commit()
        cursor.close()

        return True, data

    except sqlite3.Error as e:
        message = 'details="Error while connecting to SQLite" value="{}" ' \
                  'sql_query="{}"'.format(e, SQL_TO_ADD_EXCEPTION)
        logging.error(message)

        return False, []
