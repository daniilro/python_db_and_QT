'''


'''

import logging

DATA_PACK_SIZE = 1000
DEF_IP_ADDR = '127.0.0.1'
DEF_PORT = 7777

ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
#RESPONSE = 'response'
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
TIME = 'time'
RESP_OK = {RESPONSE: 200}
BASE_ERROR_NAME='Bad Request'
RESP_ERROR = {RESPONSE: 400, ERROR: 'Bad Request'}
TEST_TIME = "1.1"
DEF_USER="Guest"
SENDER="user"
DEFAULT_ENCODING='UTF-8'
ENCODING=DEFAULT_ENCODING
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
ACCOUNT_NAME = 'account_name'
MAX_CONNECTIONS = 100
#DEF_USER
SENDER = 'from'
DESTINATION = 'to'
EXIT = 'exit'
LIST_INFO = 'data_list'


RESPONSE_200 = {RESPONSE: 200}
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}
RESPONSE_202 = {RESPONSE: 202,
                LIST_INFO:None
                }


DEF_TIMEOUT = 2

SERVER_DATABASE = 'sqlite:///server_db.db3'

LOGGING_LEVEL = logging.DEBUG

SERVER_GUI='Y'

GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'