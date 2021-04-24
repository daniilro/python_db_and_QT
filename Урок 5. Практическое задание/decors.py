'''


'''

import sys
import logging
import log.config.config_server_log
import log.config.config_client_log
import traceback
import inspect

if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')

def log(func_to_log):

    def logger(*args, **kwargs):
#        LOGGER.debug(f"Calling function {func_to_log.__name__} form {func_to_log.__module__}")
        LOGGER.debug(f'Была вызвана функция {func_to_log.__name__} c параметрами {args}, {kwargs}. '
                     f'Вызов из модуля {func_to_log.__module__}. Вызов из'
                     f' функции {traceback.format_stack()[0].strip().split()[-1]}.'
                     f'Вызов из функции {inspect.stack()[1][3]}')
        ret = func_to_log(*args, **kwargs)
        LOGGER.debug(f"{func_to_log.__name__} finished")
        return ret
    return logger
