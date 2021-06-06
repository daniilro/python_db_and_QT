'''


'''

import inspect
import socket
import logging
import sys
import traceback

import log.config.config_client_log
import log.config.config_server_log

from common_defs import *

sys.path.append('../')

#from core import MessageProcessor
from common_defs import ACTION, PRESENCE



if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def log(func_to_log):
    def logger(*args, **kwargs):
        #        LOGGER.debug(f"Calling function {func_to_log.__name__} form {func_to_log.__module__}")
        LOGGER.debug(
            f'Была вызвана функция {func_to_log.__name__} c параметрами {args}, {kwargs}. '
            f'Вызов из модуля {func_to_log.__module__}. Вызов из'
            f' функции {traceback.format_stack()[0].strip().split()[-1]}.'
            f'Вызов из функции {inspect.stack()[1][3]}')
        ret = func_to_log(*args, **kwargs)
        LOGGER.debug(f"{func_to_log.__name__} finished")
        return ret

    return logger

def login_required(func):
    '''
    Декоратор, проверяющий, что клиент авторизован на сервере.
    Проверяет, что передаваемый объект сокета находится в
    списке авторизованных клиентов.
    За исключением передачи словаря-запроса
    на авторизацию. Если клиент не авторизован,
    генерирует исключение TypeError
    '''

    def checker(*args, **kwargs):
        # проверяем, что первый аргумент - экземпляр MessageProcessor
        # Импортить необходимо тут, иначе ошибка рекурсивного импорта.
        from core import MessageProcessor
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # Проверяем, что данный сокет есть в списке names класса
                    # MessageProcessor
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            # Теперь надо проверить, что передаваемые аргументы не presence
            # сообщение. Если presense, то разрешаем
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            # Если не не авторизован и не сообщение начала авторизации, то
            # вызываем исключение.
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker