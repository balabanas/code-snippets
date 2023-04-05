import json
import subprocess
import unittest

import requests

from scoring_api import store
from scoring_api.tests import utils

"""Run api.py in subprocess, make requests and evaluate responses"""
"""Tests require Redis instance up an running"""


class RequestResponseTest(unittest.TestCase):
    def setUp(self) -> None:
        redis_db_idx = 1
        db = store.RedisStorage(db_idx=redis_db_idx)
        db.connect()
        db.rs.sendall('FLUSHDB\r\n'.encode())
        db.rs.recv(1024)  # clear buffer
        fixture_lists: dict = {
            'i:0': ["cars", "pets"],
            'i:1': ["sport", "geek"],
            'i:2': ["hi-tech", "sport"],
            'i:3': ["cars", "pets"],
        }
        for k, v in fixture_lists.items():
            db.rpush(k, v)
        db.close_connection()

        http_server_host = 'localhost'
        http_server_port = 8080
        self.request = {
            "account": "testacc",
            "login": "testlog",
        }
        utils.set_valid_auth(self.request)
        self.url = f'http://{http_server_host}:{http_server_port}/method'
        self.headers = {'Content-Type': 'application/json'}
        self.process = subprocess.Popen(['python', '-m', 'scoring_api.api', f'--redisdb={redis_db_idx}', '--log=scoring_api/log.txt'])

    def tearDown(self) -> None:
        self.process.terminate()

    def test_ok_online_score(self):
        self.request['method'] = 'online_score'
        self.request['arguments'] = {"phone": 18888824088, "email": "test@mail.com"}
        response = requests.post(self.url, headers=self.headers, data=json.dumps(self.request))
        self.assertEqual('{"response": {"score": 3.0}, "code": 200}', response.text)

    def test_online_score_success_no_method(self):
        self.request['arguments'] = {"phone": 18888824088, "email": "test@mail.com"}
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
        self.assertIn('Field `date` should be a str formatted', response.text)
