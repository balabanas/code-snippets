import json
import os
import time
import unittest

import requests

from scoring_api import api


class RequestResponseTest(unittest.TestCase):
    def setUp(self) -> None:
        import subprocess
        print('CWD: ', os.getcwd())
        self.process = subprocess.Popen(['python', '../../api.py'])

    def tearDown(self) -> None:
        self.process.terminate()

    def test_online_score_success(self):
        url = 'http://localhost:8080/method'  # TODO: parametrize
        headers = {'Content-Type': 'application/json'}
        data = {"account": "testacc", "login": "testlog", "method": "online_score",  # TODO construct valid token
                "token": "d0ffdbabce6b9ceb5f95127347a501c78d04592813ffbb4eae224ed18f838998e0ea214d382fab2a69712d433aab30259abd1f99734da71440dc270a99a5cbab",
                "arguments": {"phone": 78888824088, "email": "test@mail.ent"}}

        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(response.text)

    def test_online_clients_interests_success(self):
        url = 'http://localhost:8080/method'  # TODO: parametrize
        headers = {'Content-Type': 'application/json'}
        data = {"account": "testacc", "login": "testlog", "method": "clients_interests",  # TODO construct valid token
                "token": "d0ffdbabce6b9ceb5f95127347a501c78d04592813ffbb4eae224ed18f838998e0ea214d382fab2a69712d433aab30259abd1f99734da71440dc270a99a5cbab",
                "arguments": {"client_ids": [1, 2, 10, 25], "date": "22.03.1996"}}

        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(response.text)
