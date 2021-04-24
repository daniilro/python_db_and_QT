"""


"""

import json

from common_defs import DATA_PACK_SIZE, DEFAULT_ENCODING
from errors import IncorrectDataRecivedError, NonDictInputError


######################################################################
# @log
def get_my_message(client):
    encoded_response = client.recv(DATA_PACK_SIZE)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(DEFAULT_ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise IncorrectDataRecivedError
    else:
        raise IncorrectDataRecivedError


######################################################################
# @log
def send_message(sock, message):
    if not isinstance(message, dict):
        raise NonDictInputError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(DEFAULT_ENCODING)
    sock.send(encoded_message)

######################################################################
