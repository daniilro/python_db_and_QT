'''


'''

import logging
import sys

###########################################################
if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


###########################################################
class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            LOGGER.critical(
                f'Incorrect port number {value}. Must be from 1024 to 65535.')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
