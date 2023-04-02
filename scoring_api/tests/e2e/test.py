import json
import subprocess
import unittest

import requests

from scoring_api.tests import utils

"""Run api.py in subprocess, make requests and evaluate responses"""
"""Tests require Redis instance up an running"""


class RequestResponseTest(unittest.TestCase):
    def setUp(self) -> None:
        redis_db_idx = 1
        http_server_host = 'localhost'
        http_server_port = 8080
        self.request = {
            "account": "testacc",
            "login": "testlog",
        }
        utils.set_valid_auth(self.request)
        self.url = f'http://{http_server_host}:{http_server_port}/method'
        self.headers = {'Content-Type': 'application/json'}
        self.process = subprocess.Popen(['python', 'api.py', f'--redisdb={redis_db_idx}'])

    def tearDown(self) -> None:
        self.process.terminate()

    def test_ok_online_score(self):
        self.request['method'] = 'online_score'
        self.request['arguments'] = {"phone": 78888824088, "email": "test@mail.ent"}
        response = requests.post(self.url, headers=self.headers, data=json.dumps(self.request))
        self.assertEqual('{"response": {"score": 3.0}, "code": 200}', response.text)

    def test_online_score_success_no_method(self):
        self.request['arguments'] = {"phone": 78888824088, "email": "test@mail.ent"}
        response = requests.post(self.url, headers=self.headers, data=json.dumps(self.request))
        self.assertEqual('{"error": "Field `method` is required!", "code": 422}', response.text)

    def test_ok_online_clients_interests(self):
        self.request['method'] = 'clients_interests'
        self.request['arguments'] = {"client_ids": [1, 2], "date": "22.03.1996"}
        response = requests.post(self.url, headers=self.headers, data=json.dumps(self.request))
        self.assertEqual('{"response": {"1": ["sport", "geek"], "2": ["hi-tech", "sport"]}, "code": 200}',
                         response.text)

    def test_online_clients_interests_bad_date(self):
        self.request['method'] = 'clients_interests'
        self.request['arguments'] = {"client_ids": [1, 2], "date": "221996"}
        response = requests.post(self.url, headers=self.headers, data=json.dumps(self.request))
        self.assertIn('Field date should be a str formatted', response.text)
