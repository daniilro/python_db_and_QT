import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
import json
from common_defs import PRESENCE, DEF_USER, TEST_TIME

from client import create_presence_message, process_answer


###############################################################
class TestClass(unittest.TestCase):

    ###############################################################
    def test_create_presence_message(self):
        print("test_create_presence_message")
        test = create_presence_message()

        message = json.dumps({
            "action": PRESENCE,
            "time": TEST_TIME,
            "type": "status",
            "user": {
                "account_name": DEF_USER,
                "status": "Yep, I am here!!!"
            }
        }, indent=4)

        message2sand: bytes = message.encode('utf-8')

        self.assertEqual(test, message2sand)

    ###############################################################
    def test_process_answer_200(self):
        self.assertEqual(process_answer(b'{\n    "response": 200\n}'), '200 : OK')

    ###############################################################
    def test_process_answer_400(self):
        self.assertNotEqual(process_answer(b'{\n    "response": 400,\n    "error": "Bad Request"\n}'), '200 : OK')

    ###############################################################
    def test_process_answer_400(self):
        self.assertEqual(process_answer(b'{\n    "response": 400,\n    "error": "Bad Request"\n}'), '400 : Bad Request')


###############################################################

if __name__ == '__main__':
    unittest.main()
