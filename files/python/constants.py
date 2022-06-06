########################################################################################################################

""" MISP Broker constants """

# Mode settings
RUN_MODE = {
    'SERVER': 'SERVER',
    'AGENT': 'AGENT',
    'DUAL': 'DUAL'
}

SIEM_LIST = ['QRADAR', 'SPLUNK', 'CSV']

# Application Identification on SIEM
APPLICATION_NAME = 'MISP Broker SOC TSI'

# File settings
BROKER_SETTING_FILE = 'settings.cfg'
MESSAGE_FILE = 'message_file.txt'
TYPE_LIST = 'type_list.txt'
RUNNING_FILE_CONTENT = 'Started at: {}\nDelete this file to stop the agent service.'
BROKER_SETTINGS = 'settings.cfg'

# Hashs
HASH_TYPES = ['sha1', 'sha256', 'sha3-384', 'sha512', 'imphash', 'md5']

# IP
IP_TYPES = ['ip-dst', 'ip-src']
REGEX_IPV4 = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'

# Time and date settings
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
HOURS_IN_DAY = 24

# Logging settings
LOG_OUTPUT_FORMAT = 'timestamp="%(asctime)s" severity="%(levelname)s" func="%(funcName)s" %(message)s'
LOG_MODE = 'a'

# Local database settings
DATABASE_INITIALIZER_agent_iocs = 'CREATE TABLE "agent_iocs" ( \
                        "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
                        "type"	TEXT NOT NULL, \
                        "value"	TEXT NOT NULL, \
                        "sync_misp_timestamp"	TEXT NOT NULL, \
                        "attribute_timestamp"	TEXT NOT NULL, \
                        "sync_siem_status"	INTEGER NOT NULL DEFAULT 0, \
                        "sync_siem_timestamp"	TEXT NOT NULL DEFAULT "Not synchronized", \
                        "lived_days"	INTEGER NOT NULL DEFAULT 0, \
                        "purged_siem_status"	INTEGER NOT NULL DEFAULT 0, \
                        "purged_siem_timestamp"	TEXT NOT NULL DEFAULT "Not purged", \
                        "false_positive"	INTEGER NOT NULL DEFAULT 0, \
                        "md5"	TEXT NOT NULL UNIQUE \
                    );'

DATABASE_INITIALIZER_agent_last_sync = 'CREATE TABLE "agent_last_sync" ( \
                        "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
                        "type"	TEXT NOT NULL UNIQUE, \
                        "sync_misp_timestamp"	TEXT NOT NULL \
                    );'

DATABASE_INITIALIZER_execution_history = 'CREATE TABLE "execution_history" ( \
                        "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
                        "mode"	TEXT NOT NULL, \
                        "start"	TEXT NOT NULL, \
                        "stop"	TEXT NOT NULL DEFAULT "Not finished", \
                        "total_time"	TEXT NOT NULL DEFAULT "Not finished", \
                        "status"	TEXT NOT NULL DEFAULT "Started" \
                    );'

DATABASE_INITIALIZER_connection_errors = 'CREATE TABLE "connection_errors" ( \
                        "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
                        "destination"	TEXT NOT NULL, \
                        "timestamp"	TEXT NOT NULL, \
                        "details"	TEXT NOT NULL \
                    );'

DATABASE_INITIALIZER_agent_siem_storage = 'CREATE TABLE "agent_siem_storage" ( \
                        "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
                        "type"	TEXT NOT NULL, \
                        "siem_storage"	TEXT NOT NULL, \
                        "created_status"	INTEGER NOT NULL DEFAULT 0, \
                        "created_timestamp"	TEXT NOT NULL, \
                        "sync_siem_timestamp"	TEXT NOT NULL DEFAULT "Not synchronized", \
                        "purged_siem_timestamp"	TEXT NOT NULL DEFAULT "Not purged" \
                    );'

DATABASE_INITIALIZER_lived_days_update_history = 'CREATE TABLE "lived_days_update_history" ( \
                                                        "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
                                                        "timestamp"	TEXT NOT NULL \
                                                    );'

DATABASE_INITIALIZER_exceptions = 'CREATE TABLE "exceptions" ( \
                                        "id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, \
                                        "timestamp"	TEXT NOT NULL, \
                                        "reported"	INTEGER NOT NULL DEFAULT 0, \
                                        "details"	TEXT NOT NULL \
                                    );'

# Local database query
SQL_TO_SHOW_VERSION = 'select sqlite_version();'

# SQL for agent_iocs
SQL_TO_LIST_ALL_IOCS = 'SELECT * FROM agent_iocs WHERE false_positive = 0;'
SQL_TO_LIST_IOCS = 'SELECT id, type, value, sync_siem_status FROM agent_iocs WHERE (sync_siem_status = 0 OR purged_siem_status = 1) AND false_positive = 0 AND lived_days <= ? AND type = ?; '
SQL_TO_CHECK_SYNCED_IOC = 'SELECT id, type, value, sync_siem_status FROM agent_iocs WHERE sync_siem_status = 1 AND purged_siem_status = 0 AND false_positive = 0 AND value = ? AND type = ?; '
SQL_TO_UPDATE_ADD_ITEM = 'UPDATE agent_iocs SET purged_siem_status = 0, purged_siem_timestamp = "Not purged", sync_siem_status = 1, false_positive = 0, sync_siem_timestamp = ? WHERE type = ? AND value = ?;'
SQL_TO_LIST_TYPES_IN_DB = 'SELECT type FROM agent_iocs WHERE false_positive = 0 AND sync_siem_status = 1 GROUP BY type;'
SQL_TO_UPDATE_PURGED_TYPE = 'UPDATE agent_iocs SET sync_siem_status = 0, purged_siem_status = 1, purged_siem_timestamp = ? WHERE type = ?;'
SQL_TO_UPDATE_PURGED_ITEM = 'UPDATE agent_iocs SET purged_siem_status = 1, sync_siem_status = 0, purged_siem_timestamp = ? WHERE type = ? AND value = ? AND purged_siem_status = 0; '
SQL_TO_LIST_ITEM_TO_REMOVE = 'SELECT id, type, value, sync_siem_status, false_positive FROM agent_iocs WHERE sync_siem_status = 1 AND purged_siem_status = 0 AND type = ? AND (lived_days > ? OR false_positive = 1);'
SQL_TO_LIST_ALL_DATE_GROUPS = 'SELECT attribute_timestamp, lived_days FROM agent_iocs WHERE false_positive = 0 GROUP BY attribute_timestamp, lived_days;'
SQL_TO_UPDATE_LIVED_DAYS_OF_IOCS = 'UPDATE agent_iocs SET lived_days = ? WHERE attribute_timestamp like ? AND lived_days = ?;'
SQL_TO_GET_IOC_BY_MD5 = 'SELECT value FROM agent_iocs WHERE md5 = ?'
SQL_TO_ADD_IOC = 'INSERT INTO agent_iocs (type, value, sync_misp_timestamp, attribute_timestamp, md5, lived_days) VALUES (?, ?, ?, ?, ?, ?);'
SQL_TO_LIST_ALL_IOCS_NOT_FALSE_POSITIVE = 'SELECT value FROM agent_iocs WHERE sync_siem_status = 1 AND purged_siem_status = 0 AND false_positive = 0 AND type = ? AND lived_days <= ?;'
SQL_TO_ADD_IOC_EXCEPTION = 'INSERT INTO agent_iocs (false_positive, sync_siem_status, type, value, sync_misp_timestamp, attribute_timestamp, md5, lived_days) VALUES (1, 1, ?, ?, ?, ?, ?, ?);'
SQL_TO_GET_IOC_BEFORE_DELETE = 'SELECT * FROM agent_iocs WHERE type = ? AND value = ?;'
SQL_TO_DELETE_IOC_BEFORE_EXCEPTION = 'DELETE FROM agent_iocs WHERE type = ? AND value = ?;'
SQL_TO_UPDATE_IOC_AS_FALSE_POSITIVE = 'UPDATE agent_iocs SET sync_siem_status = 0, purged_siem_status = 1, false_positive = 1, purged_siem_timestamp = ? WHERE type = ? AND lived_days <= ? AND value {} ?;'

# SQL for agent_siem_storage
SQL_TO_UPDATE_PURGED_SIEM_STORAGE = 'UPDATE agent_siem_storage SET created_status = 0, purged_siem_timestamp = ? WHERE type = ?;'
SQL_TO_CHECK_SIEM_STORAGE_IN_DB = 'SELECT type FROM agent_siem_storage WHERE type = ?;'
SQL_TO_ADD_SIEM_STORAGE_IN_DB = 'INSERT INTO agent_siem_storage (type, siem_storage, created_status, created_timestamp) VALUES (?, ?, ?, ?);'
SQL_TO_UPDATE_LAST_SYNC_SIEM_STORAGE = 'UPDATE agent_siem_storage SET sync_siem_timestamp = ? WHERE type = ?'
SQL_TO_GET_ALL_KV_NAMES = 'SELECT siem_storage FROM agent_siem_storage; '

# SQL for lived_days_update_history
SQL_TO_LIST_LIVED_DAYS_UPDATE = 'SELECT timestamp FROM lived_days_update_history;'
SQL_TO_ADD_LIVED_DAYS_HISTORY = 'INSERT INTO lived_days_update_history (timestamp) VALUES (?);'

# SQL for execution_history
SQL_TO_ADD_EXECUTION_HISTORY = 'INSERT INTO execution_history (mode, start) VALUES (?, ?);'
SQL_TO_GET_ID_OF_EXECUTION_HISTORY = 'SELECT id FROM execution_history WHERE mode = ? AND start = ?;'
SQL_TO_GET_DATA_OF_EXECUTION_HISTORY = 'SELECT * FROM execution_history WHERE id = ?;'
SQL_TO_GET_START_EXECUTION = 'SELECT start FROM execution_history WHERE id = ?;'
SQL_TO_UPDATE_EXECUTION_HISTORY = 'UPDATE execution_history SET stop = ?, total_time = ?, status = ? WHERE id = ?;'

# SQL for connection_errors
SQL_TO_ADD_CONNECTION_ERROR = 'INSERT INTO connection_errors (destination, timestamp, details) VALUES (?, ?, ?);'
SQL_TO_GET_CONNECTION_ERROR = 'SELECT id FROM connection_errors WHERE destination = ? AND timestamp = ? AND details = ?;'
SQL_TO_GET_DATA_CONNECTION_ERROR = 'SELECT * FROM connection_errors WHERE id = ?;'

# SQL for agent_last_sync
SQL_TO_ADD_LAST_SYNC = 'INSERT INTO agent_last_sync (type, sync_misp_timestamp) VALUES (?, ?);'
SQL_TO_GET_LAST_SYNC = 'SELECT sync_misp_timestamp FROM agent_last_sync WHERE type = ?;'
SQL_TO_UPDATE_LAST_SYNC = 'UPDATE agent_last_sync SET sync_misp_timestamp = ? WHERE type = ?;'

# SQL for exceptions
SQL_TO_ADD_EXCEPTION = 'INSERT INTO exceptions (timestamp, details) VALUES (?, ?);'

# Help settings
TYPE_LIST_HELP = 'Please, config the file {}.'.format(TYPE_LIST)
SIEM_HELP = 'SIEM {} in settings.cfg is not available, please, choose: {}'.format('{}', SIEM_LIST)
CODENAME_HELP = 'Please, give the customer code name as argument. Example: python3 {} {}'

# Auto type list settings
TYPE_LIST_SAMPLE = '# type ttl element_type\n' \
                   '# \n' \
                   '# Set the TTL using a number to represent days.\n' \
                   '# 30 equal 30 days of time to live.\n' \
                   '# You can change the default value in variable DEFAULT_TTL in {}.\n' \
                   '# Use 0 to define the type as all time. You can change the initial date in variable START_DATE in {}.\n' \
                   '# \n' \
                   '# element_type is one of this: ALN, NUM, IP, ALNIC.\n' \
                   '# \n' \
                   '# Example:\n' \
                   '# md5 0 ALN\n' \
                   '# filename 0 ALNIC\n' \
                   '# ip-dst 30 IP\n' \
                   '# \n' \
                   '# To ignore a type just insert a # in the start of the line, example: #domain 0 ALNIC\n' \
                   '# \n' \
                   '# List of some available IOC types:\n' \
                   'ip-src 30 IP\n' \
                   'ip-dst 90 IP\n' \
                   'ip-dst|port 90 ALN\n' \
                   'email-src 90 ALNIC\n' \
                   'email-src-display-name 90 ALNIC\n' \
                   'email-subject 90 ALNIC\n' \
                   'domain 182 ALNIC\n' \
                   'domain|ip 182 ALNIC\n' \
                   'hostname 182 ALNIC\n' \
                   'uri 365 ALNIC\n' \
                   'url 365 ALNIC\n' \
                   'filename 0 ALNIC\n' \
                   'filename|md5 0 ALN\n' \
                   'filename|sha1 0 ALN\n' \
                   'filename|sha256 0 ALN\n' \
                   'imphash 0 ALN\n' \
                   'md5 0 ALN\n' \
                   'sha1 0 ALN\n' \
                   'sha256 0 ALN\n' \
                   'sha3-384 0 ALN\n' \
                   'sha512 0 ALN\n' \
                   'ssdeep 0 ALN\n' \
                   'user-agent 0 ALNIC\n' \
                   'vulnerability 0 ALNIC\n' \
                   '# AS\n' \
                   '# attachment\n' \
                   '# btc\n' \
                   '# comment\n' \
                   '# datetime\n' \
                   '# email-attachment\n' \
                   '# email-dst\n' \
                   '# float\n' \
                   '# link\n' \
                   '# malware-sample\n' \
                   '# mime-type\n' \
                   '# mutex\n' \
                   '# named pipe\n' \
                   '# other\n' \
                   '# pattern-in-file\n' \
                   '# pattern-in-traffic\n' \
                   '# pdb\n' \
                   '# port\n' \
                   '# regkey\n' \
                   '# regkey|value\n' \
                   '# sigma\n' \
                   '# size-in-bytes\n' \
                   '# snort\n' \
                   '# telfhash\n' \
                   '# threat-actor\n' \
                   '# tlsh\n' \
                   '# whois-registrant-email\n' \
                   '# x509-fingerprint-sha1\n' \
                   '# yara\n'.format(BROKER_SETTING_FILE, BROKER_SETTING_FILE)

########################################################################################################################

