import datetime
import functools
import json
import unittest
from unittest.mock import Mock

from scoring_api import api
from scoring_api import store
from scoring_api.tests import utils


def cases(cases_list: list):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for c in cases_list:
                new_args = args + (c if isinstance(c, tuple) else (c,))
                f(*new_args)
        return wrapper
    return decorator


class CharFieldTest(unittest.TestCase):
    """Tests for field descriptors. How validation works"""
    def setUp(self):
        class ClassWithFields:
            nf_chf = api.CharField(required=False, nullable=True)
            nnf_chf = api.CharField(required=False, nullable=False)
            af = api.ArgumentsField(required=True, nullable=True)
            ef = api.EmailField(required=True, nullable=True)
            pf = api.PhoneField(required=True, nullable=True)
            df = api.DateField(required=True, nullable=True)
            bdf = api.BirthDayField(required=True, nullable=True)
            gf = api.GenderField(required=True, nullable=True)
            cif = api.ClientIDsField(required=True, nullable=True)
        self.instance_with_fields = ClassWithFields()

    def test_validate_nullable(self):  # this also tests descriptors and BaseField class
        setattr(self.instance_with_fields, 'nf_chf', None)
        self.assertEqual(None, getattr(self.instance_with_fields, 'nf_chf'))

        setattr(self.instance_with_fields, 'nf_chf', 'something nf')
        self.assertEqual('something nf', getattr(self.instance_with_fields, 'nf_chf'))

        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'nnf_chf', None)

        setattr(self.instance_with_fields, 'nnf_chf', 'something nnf')
        self.assertEqual('something nnf', getattr(self.instance_with_fields, 'nnf_chf'))

    def test_validate_char_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'nf_chf', 3)

    def test_validate_arguments_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'af', 3)  # dict expected
        setattr(self.instance_with_fields, 'af', {})
        self.assertEqual({}, getattr(self.instance_with_fields, 'af'))

    def test_validate_email_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'ef', 'ds @motw.net')  # invalid email
        setattr(self.instance_with_fields, 'ef', 'ds@motw.net')
        self.assertEqual('ds@motw.net', getattr(self.instance_with_fields, 'ef'))

    def test_validate_phone_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'pf', 'not a phone number')  #
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'pf', '12345678900')  # not starting with 7
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'pf', '7123456789')  # not 11
        setattr(self.instance_with_fields, 'pf', '71234567890')  # accepts strings
        self.assertEqual('71234567890', getattr(self.instance_with_fields, 'pf'))
        setattr(self.instance_with_fields, 'pf', 71234567890)  # accepts numbers
        self.assertEqual(71234567890, getattr(self.instance_with_fields, 'pf'))

    def test_validate_date_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'df', '11.11.11')  # not dd.mm.yyyy format
        setattr(self.instance_with_fields, 'df', '11.11.2011')
        self.assertEqual(datetime.date(2011, 11, 11), getattr(self.instance_with_fields, 'df'))

    def test_validate_birthdate_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'bdf', '01.01.1900')  # age > 70
        setattr(self.instance_with_fields, 'bdf', '11.11.2011')
        self.assertEqual(datetime.date(2011, 11, 11), getattr(self.instance_with_fields, 'bdf'))

    def test_validate_gender_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'gf', '2')  # NaN
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'gf', 11)  # not in the list
        setattr(self.instance_with_fields, 'gf', 2)
        self.assertEqual(2, getattr(self.instance_with_fields, 'gf'))

    def test_validate_client_ids_type(self):
        with self.assertRaises(TypeError):
            setattr(self.instance_with_fields, 'cif', '[1, 2, 3]')  # not a list
        setattr(self.instance_with_fields, 'cif', [1, 2, 3])
        self.assertEqual([1, 2, 3], getattr(self.instance_with_fields, 'cif'))


class TestSuite(unittest.TestCase):
    """Tests for Request classes"""
    def setUp(self):
        # Mocking store: Redis instance is not required
        redis_storage = Mock(spec=store.RedisStorage)
        redis_storage.get.return_value = json.dumps(['cars', 'pets'])
        redis_storage.cache_get.return_value = 3.0

        self.context = {}
        self.headers = {}
        self.settings = redis_storage

    def tearDown(self) -> None:
        # self.rs.close_connection()
        pass

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.settings)

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ])
    def test_bad_auth(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "method": None, "arguments":
            {"phone": "79175002040", "email": "stupnikovotus.ru"}},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ])
    def test_invalid_method_request(self, request):
        utils.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @cases([
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000", "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "s", "last_name": 2},
        {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ])
    def test_invalid_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        utils.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        utils.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    def test_ok_score_admin_request(self):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        utils.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases([
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
        {"client_ids": ["1", "2", "10", "25"], "date": "22.03.1996"},
    ])
    def test_invalid_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        utils.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        utils.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, (bytes, str)) for i in v)
                        for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))


if __name__ == "__main__":
    unittest.main()
