'''
config_client_log
'''
import os
import sys

from common_defs import LOGGING_LEVEL
import logging

sys.path.append(os.path.join(os.getcwd(), '..'))



#################################################################

CLIENT_FORAMTTER = logging.Formatter(
    '%(asctime)-25s %(levelname)-10s  pid: %(process)d %(filename)s line: %(lineno)d %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, '../log/client.log')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(CLIENT_FORAMTTER)
# STREAM_HANDLER.setLevel(logging.ERROR)
LOG_FILE = logging.FileHandler(PATH, encoding='utf8')
LOG_FILE.setFormatter(CLIENT_FORAMTTER)

LOGGER = logging.getLogger('client')
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(LOG_FILE)
LOGGER.setLevel(LOGGING_LEVEL)

#################################################################
if __name__ == '__main__':
    LOGGER.critical('Всё очень плохо')
    LOGGER.error('Всё плохо')
    LOGGER.warning('Что-то не так')
    LOGGER.info('Тут вот что...')
    LOGGER.debug('Я волнуюсь')
