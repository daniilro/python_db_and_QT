import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
import getpass
from common_defs import ACCOUNT_NAME, DEF_USER, RESPONSE, ERROR, PRESENCE, ACTION, TIME, USER, TEST_TIME, RESP_OK, \
    RESP_ERROR

from server import process_client_message


#################################################################
class TestServer(unittest.TestCase):

    #################################################################
    def test_all_is_fine(self):
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE,
             TIME: TEST_TIME,
             USER: {ACCOUNT_NAME: DEF_USER}}),
            RESP_OK)

    #################################################################
    def test_no_time(self):
        self.assertEqual(process_client_message(
            {ACTION: PRESENCE,
             USER: getpass.getuser()}),
            RESP_ERROR)

    #################################################################
    def test_no_action(self):
        self.assertEqual(process_client_message(
            {'time': '1.1', 'user': {"account_name": getpass.getuser()}}), {RESPONSE: 400, ERROR: 'Bad Request'})


#################################################################
if __name__ == '__main__':
    unittest.main()
