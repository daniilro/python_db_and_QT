'''


'''

from common_defs import LOGGING_LEVEL
import logging.handlers
import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))


SERVER_FORMATTER = logging.Formatter(
    '%(asctime)-25s %(levelname)-10s  pid: %(process)d %(filename)s line: %(lineno)d %(message)s')


PATH = os.getcwd()
PATH = os.path.join(PATH, '../log/server.log')


STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(SERVER_FORMATTER)
# STREAM_HANDLER.setLevel(logging.ERROR)
LOG_FILE = logging.handlers.TimedRotatingFileHandler(
    PATH, encoding='utf8', interval=1, when='midnight')
LOG_FILE.setFormatter(SERVER_FORMATTER)

LOGGER = logging.getLogger('server')
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(LOG_FILE)
LOGGER.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    LOGGER.critical('Всё очень плохо')
    LOGGER.error('Всё плохо')
    LOGGER.warning('Что-то не так')
    LOGGER.info('Тут вот что...')
    LOGGER.debug('Я волнуюсь')
