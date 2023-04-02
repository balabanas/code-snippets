#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import datetime
import hashlib
import json
import logging
import re
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Union

from scoring_api.scoring import get_interests, get_score
from scoring_api.store import RedisStorage

SALT = "somestring"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class BaseField:
    """Field general class, with descriptors and validation for Null"""
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def __set_name__(self, owner, name):
        self.name = '_' + name

    def __get__(self, instance, owner):
        return getattr(instance, self.name)

    @staticmethod
    def validate_nullable(field, value):
        if not field.nullable and value is None:
            raise TypeError(f"Field {field.name[1:]} is not nullable.")


class CharField(BaseField):
    """Storage for general char arguments, with validating descriptor"""
    def __set__(self, instance, value):
        self.validate_nullable(self, value)
        if not isinstance(value, (str, type(None))):
            raise TypeError(f"If being set, field {self.name[1:]} expects string. Got: {type(value)}")
        setattr(instance, self.name, value)


class ArgumentsField(BaseField):
    """Storage for arguments dict, with validating descriptor"""
    def __set__(self, instance, value):
        self.validate_nullable(self, value)
        if not isinstance(value, (dict, type(None))):
            raise TypeError(f"If being set, field {self.name[1:]} expects to be dict. Got: {type(value)}")
        setattr(instance, self.name, value)


class EmailField(CharField):
    """Storage for email argument, with validating descriptor"""
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(pattern, value) is None:
                raise TypeError(f"Field {self.name[1:]} dose not meet e-mail format")


class PhoneField(BaseField):
    """Storage for phone argument, with validating descriptor"""
    def __set__(self, instance, value):
        self.validate_nullable(self, value)
        if value:
            if str(value)[0] != '7':
                raise TypeError(
                    f"Field {self.name[1:]} should start with 7")
            if len(str(value)) != 11:
                raise TypeError(
                    f"Field {self.name[1:]} should have exactly 11 digits")
        setattr(instance, self.name, value)


class DateField(BaseField):
    """Storage for date argument, with validating descriptor"""
    def __set__(self, instance, value):
        self.validate_nullable(self, value)
        if value:
            try:
                date = datetime.datetime.strptime(value, '%d.%m.%Y').date()
                setattr(instance, self.name, date)
            except ValueError:
                raise TypeError(f"Field {self.name[1:]} should be a str formatted as dd.mm.yyyy. Got: {value}")


class BirthDayField(DateField):
    """Storage for birthday argument, with validating descriptor"""
    def __set__(self, instance, value):
        super().__set__(instance, value)
        date = getattr(instance, self.name)  # value was already set by super method, take it
        if date:
            age = datetime.datetime.today().date() - date
            if age > datetime.timedelta(days=365 * 70):
                raise TypeError(f"Field {self.name[1:]} should be < 70 years behind current date. Got: {date}")


class GenderField(BaseField):
    """Storage for gender argument, with validating descriptor"""
    def __set__(self, instance, value):
        self.validate_nullable(self, value)
        if not isinstance(value, (int, float, type(None))):
            raise TypeError(f"If being set, {self.name[1:]} should be a number")
        if value and value not in [0, 1, 2]:
            raise TypeError(f"If being set, {self.name[1:]} expects one of {{0, 1, 2}}. Got: {value}")
        setattr(instance, self.name, value)


class ClientIDsField(BaseField):
    """Storage for client IDs list, with validating descriptor"""
    def __set__(self, instance, value):
        self.validate_nullable(self, value)
        if not isinstance(value, (list, type(None))):
            raise TypeError(f"If being set, {self.name[1:]} expects list. Got: {type(value)}")
        elif isinstance(value, list):
            if len(value) == 0:
                raise TypeError(f"Field {self.name[1:]} expects non-empty list. Got: {value}")
        if value:
            for el in value:
                if not isinstance(el, (int, float)):
                    raise TypeError(f"Field {self.name[1:]} expects numbers in a list. Got: {type(el)}")
        setattr(instance, self.name, value)


class CollectFieldsMeta(type):
    """Collects *Field-class attributes of a Class, as defined in `field_classes`,
    into a list, available as an attribute of a Class instance. Affords easy iteration over
    attributes (Fields that are expected in a request, differ from Class to a Class)"""
    field_classes = (CharField, DateField, PhoneField, GenderField, ArgumentsField, ClientIDsField)

    def __new__(mcs, name, bases, attrs):
        request_fields = []
        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, mcs.field_classes):
                request_fields.append(attr_name)
        attrs['request_fields'] = request_fields
        return super().__new__(mcs, name, bases, attrs)


class BaseRequest(metaclass=CollectFieldsMeta):
    """Parent class that defines response and code attributes, and initialize class internalizing request, context and
     store number"""
    def __init__(self, params, ctx, store):
        self.response: Union[str, dict] = {}
        self.code: int = OK
        self.params: dict = params
        self.ctx = ctx
        self.store = store

    def _validate_required_fields(self):
        """Cycle through the fields defined in a Request class, and make sure if all of them
        that marked `required` are set from the request"""
        for f in self.request_fields:
            if self.__class__.__dict__[f].required:
                try:
                    getattr(self, f'_{f}')
                except AttributeError:
                    raise TypeError(f"Field `{f}` is required!")
        return True

    def _digest_params(self, params: dict) -> None:
        """Sets params, specified in the request class, from params dict and checks that all required fields
        were set"""
        for attr_name in self.request_fields:  # first, set attributes
            if attr_name in params:
                setattr(self, attr_name, params[attr_name])
        self._validate_required_fields()  # then check if all required were set

    def process_request(self):
        return None, None


class ClientsInterestsRequest(BaseRequest):
    """Defines clients-interests scoring arguments, parses argument's dictionary and assign values,
        implements methods to validate fields, call scoring function and return response"""
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)

    def process_request(self):
        try:
            self._digest_params(self.params)
            self.ctx['nclients'] = len(self.client_ids)
            self.response, self.code = {f'{i}': get_interests(self.store, i) for i in self.client_ids}, OK
        except TypeError as e:
            self.response, self.code = e.args[0], INVALID_REQUEST
        return self.response, self.code


class OnlineScoreRequest(BaseRequest, metaclass=CollectFieldsMeta):
    """Defines online-score scoring arguments, parses argument's dictionary and assign values,
        implements methods to validate fields, call scoring function and return response"""
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def process_request(self):
        try:
            self._digest_params(self.params)

            # Some specific pairs of parameters in request should be defined for correct scoring.
            # NB! We check here not that parameters are not Null, but were they successfully set
            # previously (taking into account `required` and `nullable` properties and other validation
            # logic), or not.
            if not (all(f'_{f}' in self.__dict__ for f in ('phone', 'email'))
                    or all(f'_{f}' in self.__dict__ for f in ('first_name', 'last_name'))
                    or all(f'_{f}' in self.__dict__ for f in ('gender', 'birthday'))):
                raise TypeError("No valid pair of arguments found")

            request_fields_vals = {f: getattr(self, f) if f'_{f}' in self.__dict__ else None for f in
                                   self.request_fields}
            score = get_score(self.store, **request_fields_vals)
            self.ctx['has'] = [f for f in self.request_fields if f'_{f}' in self.__dict__]
            self.response, self.code = {'score': score}, OK
        except TypeError as e:
            self.response, self.code = e.args[0], INVALID_REQUEST
        return self.response, self.code


class MethodFactory:
    """Choose a backend implementing method requested, and pass to the corresponding class
    necessary parameters from `ba` (backend args) dict"""
    @staticmethod
    def get_method_backend(method: str, ba: dict) -> BaseRequest:
        if method == 'online_score':
            return OnlineScoreRequest(ba['arguments'], ba['ctx'], ba['store'])
        elif method == 'clients_interests':
            return ClientsInterestsRequest(ba['arguments'], ba['ctx'], ba['store'])
        else:
            raise TypeError('Unknown method')


class MethodRequest(BaseRequest, metaclass=CollectFieldsMeta):
    """Defines request fields, parses request body and assign values,
    implements methods to check if user is admin, if it is authenticated,
    fields validation, and request routing, depending on scoring method passed"""
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    def check_auth(self):
        if self.is_admin:
            msg = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
            digest = hashlib.sha512(msg.encode()).hexdigest()
        else:
            msg = self.account + self.login + SALT
            digest = hashlib.sha512(msg.encode()).hexdigest()
        if digest == self.token:
            return True
        return False

    def process_request(self):
        try:
            self._digest_params(self.params)
            if self.check_auth():
                if self.is_admin:
                    self.response, self.code = {"score": 42}, OK
                    return self.response, self.code
            else:
                self.response, self.code = "Forbidden", FORBIDDEN
                return self.response, self.code  # auth failed

            backend_args = {'arguments': self.arguments, 'ctx': self.ctx, 'store': self.store}
            print('self.store', self.store)
            mb = MethodFactory().get_method_backend(self.method, backend_args)
            self.response, self.code = mb.process_request()

        except TypeError as e:
            self.response, self.code = e.args[0], INVALID_REQUEST
        return self.response, self.code


def method_handler(request, ctx, store):
    print('store in method handler: ', store)
    params = request['body']
    r = MethodRequest(params, ctx, store)
    response, code = r.process_request()
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def __init__(self, request, client_address, server, store):
        print('Print store: ', store)
        self.store = store
        super().__init__(request, client_address, server)

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='localhost', help="Port to run the API on")
    parser.add_argument('-p', '--port', type=int, default=8080, help="Port to run the API on")
    parser.add_argument('-l', '--log', type=str, default='log.txt', help="Path to a log file")
    parser.add_argument('--redisdb', type=int, default=0, help="Redis DB index")
    parser.add_argument('--redishost', type=str, default='localhost', help="Path to a log file")
    parser.add_argument('--redisport', type=int, default=6379, help="Path to a log file")
    args: argparse.Namespace = parser.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    # rs = RedisStorage()
    # server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    redis_store = RedisStorage(args.redishost, args.redisport, args.redisdb)
    server = HTTPServer((args.host, args.port),
                        lambda *args, **kwargs: MainHTTPHandler(*args, **kwargs, store=redis_store))
    logging.info("Starting server at %s" % args.port)
    try:
        # rs.connect()
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # rs.close_connection()
        server.server_close()


if __name__ == "__main__":
    main()
