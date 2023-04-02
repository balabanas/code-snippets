import json
import unittest

from scoring_api import store

"""Testing methods of RedisStorage"""
"""Tests require Redis instance up an running"""


class StoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.store = store.RedisStorage(db_idx=1)
        self.store.connect()
        self.store.rs.sendall('FLUSHDB\r\n'.encode())
        fixture_lists: dict = {
            'i:0': ["cars", "pets"],
            'i:1': ["sport", "geek"],
            'i:2': ["hi-tech", "sport"],
            'i:3': ["cars", "pets"],
        }
        for k, v in fixture_lists.items():
            self.store.rpush(k, v)
        self.store.close_connection()

    def tearDown(self) -> None:
        if self.store.rs:
            self.store.close_connection()
            self.assertTrue(self.store.rs._closed)

    def test_fail_switching_db(self):
        self.store.connect()
        with self.assertRaises(TypeError):
            self.store.switch_db(-1)  # index out of range

    def test_fail_to_connect(self):
        self.store.port = 6380  # wrong port
        with self.assertRaises(TimeoutError):
            self.store.connect()

    def test_get_null(self):
        self.assertEqual(json.dumps(None), self.store.get('not_existing_key'))

    def test_get_success(self):
        self.assertEqual(json.dumps(["cars", "pets"]), self.store.get('i:3'))

    def test_cache_set_sucsess(self):  # get success also tested here
        self.store.cache_set('test_key', 33, 60)
        self.assertEqual('33', self.store.cache_get('test_key'))

    def test_cache_set_fail(self):
        with self.assertRaises(TypeError):
            self.store.cache_set('test_key', '33 33', 60)

    def test_cache_set_timeout(self):
        with self.assertLogs(level='ERROR') as captured:
            self.store.port = 6380
            self.store.cache_set('test_key', 2.8, 60)
        self.assertIn("ERROR:root:Timeout: cache is not ready to save to", captured.output)

    def test_cache_get_not_existing_key(self):
        self.assertEqual(None, self.store.cache_get('non_existing_key'))

    def test_cache_get_timeout(self):
        with self.assertLogs(level='ERROR') as captured:
            self.store.port = 6380
            self.store.cache_get('test_key')
        self.assertIn("ERROR:root:Timeout: cache is not ready to read from", captured.output)
