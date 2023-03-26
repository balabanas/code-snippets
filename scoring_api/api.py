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

from scoring_api.scoring import get_interests, get_score

SALT = "Otus"
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


class FieldValidationMeta(type):
    @staticmethod
    def get_name(instance, field):
        for k, v in type(instance).__dict__.items():
            if v is field:
                return k

    @classmethod
    def validate_required_null(mcs, instance, field, value):
        if not field.nullable and value is None:
            raise TypeError(f"Field {mcs.get_name(instance, field)} can't be Null. Got: {value}")
        if field.required and value is None:
            raise TypeError(f"Field {mcs.get_name(instance, field)} is required. Got: {value}")


class CharField(metaclass=FieldValidationMeta):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable
        self.value = None

    def __set__(self, instance, value):
        type(self).validate_required_null(instance, self, value)
        ornone = " or None" if self.nullable else ''
        if not isinstance(value, str) and not value is None:
            raise TypeError(f"Field {type(self).get_name(instance, self)} expects string{ornone}. Got: {value}")
        self.value = value

    def __get__(self, instance, value):
        return self.value


class ArgumentsField(metaclass=FieldValidationMeta):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def __set__(self, instance, value):
        type(self).validate_required_null(instance, self, value)
        self.value: dict = value

    def __get__(self, instance, value):
        return self.value


class EmailField(CharField):
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value is not None:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(pattern, value) is None:
                raise TypeError(f"Field {type(self).get_name(instance, self)} dose not meet e-mail format")
        self.value = value


class PhoneField(CharField, metaclass=FieldValidationMeta):
    # def __init__(self, required=False, nullable=False):
    #     self.required = required
    #     self.nullable = nullable

    def __set__(self, instance, value):
        type(self).validate_required_null(instance, self, value)
        if value:
            try:
                int(value)
            except ValueError:
                raise TypeError(
                    f"Field {type(self).get_name(instance, self)} should be an int or a str represented number")
            if str(value)[0] != '7':
                raise TypeError(
                    f"Field {type(self).get_name(instance, self)} should start with 7")
            if len(str(value)) != 11:
                raise TypeError(
                    f"Field {type(self).get_name(instance, self)} should have exactly 11 digits")
        self.value: str = value


class DateField(metaclass=FieldValidationMeta):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def __set__(self, instance, value):
        type(self).validate_required_null(instance, self, value)
        if value:
            try:
                datetime.datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                raise TypeError(
                    f"Field {type(self).get_name(instance, self)} should be str formatted as dd.mm.yyyy"
                )
        self.value: datetime.datetime = value

    def __get__(self, instance, value):
        return self.value


class BirthDayField(DateField):
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value:
            date = datetime.datetime.strptime(value, '%d.%m.%Y')
            age = datetime.datetime.today() - date
            if age > datetime.timedelta(days=365 * 70):
                raise TypeError(f"Field {type(self).get_name(instance, self)} should be < 70 years behind current date")
        self.value: datetime = value


class GenderField(metaclass=FieldValidationMeta):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def __set__(self, instance, value):
        type(self).validate_required_null(instance, self, value)
        ornone = " or None" if self.nullable else ''
        if not isinstance(value, int) and value is not None:
            raise TypeError(f"Field {type(self).get_name(instance, self)} expects int{ornone}. Got: {value}")
        if isinstance(value, int) and value not in [0, 1, 2]:
            raise TypeError(f"Field {type(self).get_name(instance, self)} expects int values of {ornone}. Got: {value}")
        self.value: int = value

    def __get__(self, instance, value):
        return self.value


class ClientIDsField(metaclass=FieldValidationMeta):
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def __set__(self, instance, value):
        type(self).validate_required_null(instance, self, value)
        ornone = " or None" if self.nullable else ''
        if not isinstance(value, list) and value is not None:
            raise TypeError(f"Field {type(self).get_name(instance, self)} expects list{ornone}. Got: {value}")
        elif isinstance(value, list):
            if len(value) == 0:
                raise TypeError(f"Field {type(self).get_name(instance, self)} expects non-empty list. Got: {value}")
        if value:
            for el in value:
                if not isinstance(el, int):
                    raise TypeError(f"Field {type(self).get_name(instance, self)} expects ints in a list. Got: {value}")
        self.value: list = value

    def __get__(self, instance, value):
        return self.value


class BaseRequest:
    response = {}
    code = OK

    def __init__(self, request, ctx, store):
        self.request = request
        self.ctx = ctx
        self.store = store


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def _validate_params(self):
        try:
            params: dict = self.request['body']['arguments']
            self.client_ids = params.get('client_ids', None)
            self.date = params.get('date', None)
        except (TypeError, AttributeError) as e:
            self.response = {"error": e}
            self.code = INVALID_REQUEST
            return False
        if self.client_ids is None:
            self.response = {"error": "No valid client_ids were requested"}
            self.code = INVALID_REQUEST
            return False
        return True

    def process_request(self):
        if self._validate_params():
            self.response = {f'{i}': get_interests(1, i) for i in self.client_ids}
            self.ctx['nclients'] = len(self.client_ids)
            self.code = OK
        return self.response, self.code


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def _validate_params(self):
        try:
            params: dict = self.request['body']['arguments']
            self.first_name = params.get('first_name', None)
            self.last_name = params.get('last_name', None)
            self.email = params.get('email', None)
            self.phone = params.get('phone', None)
            self.birthday = params.get('birthday', None)
            self.gender = params.get('gender', None)
        except (TypeError, AttributeError) as e:
            self.response = {"error": e}
            self.code = INVALID_REQUEST
            return False
        if not (self.phone and self.email or self.first_name and self.last_name or self.gender is not None and self.birthday):
            self.response = {"error": "No valid pair of arguments found"}
            self.code = INVALID_REQUEST
            return False
        return True

    def process_request(self):
        if self._validate_params():
            params_list = ['phone', 'email', 'birthday', 'gender', 'first_name', 'last_name']
            params_vals = [self.phone, self.email, self.birthday, self.gender, self.first_name, self.last_name]
            params = zip(params_list, params_vals)
            score = get_score(self.store, *params_vals)
            self.response = {'score': score}
            self.ctx['has'] = [f for f, v in params if v is not None]
            self.code = OK
        return self.response, self.code


class MethodRequest(BaseRequest):
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
        self.response = '{"error": "Forbidden"}'
        self.code = FORBIDDEN
        return False

    def _validate_params(self):
        params: dict = self.request['body']
        try:
            self.account = params.get('account', None)
            self.login = params.get('login', None)
            self.token = params.get('token', None)
            self.arguments = params.get('arguments', None)
            self.method = params.get('method', None)
        except TypeError as e:
            self.response = {"error": e}
            self.code = INVALID_REQUEST
            return False
        return True

    def process_request(self):
        if self._validate_params() and self.check_auth():
            if self.is_admin:
                self.response = {"score": 42}
                self.code = OK
                return self.response, self.code

            if self.method == 'online_score':
                osr = OnlineScoreRequest(self.request, self.ctx, self.store)
                self.response, self.code = osr.process_request()
            elif self.method == 'clients_interests':
                cir = ClientsInterestsRequest(self.request, self.ctx, self.store)
                self.response, self.code = cir.process_request()
        return self.response, self.code


def method_handler(request, ctx, store):
    r = MethodRequest(request, ctx, store)
    response, code = r.process_request()
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

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


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8080)
    parser.add_argument('-l', '--log', type=str, default=None, const='./config.ini', nargs='?', help='Path to a config file')
    args: argparse.Namespace = parser.parse_args()

    # op = OptionParser()
    # op.add_option("-p", "--port", action="store", type=int, default=8080)
    # op.add_option("-l", "--log", action="store", default=None)
    # (opts, args) = op.parse_args()
    # logging.basicConfig(filename=opts.log, level=logging.INFO,
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    # server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    # server = HTTPServer(("localhost", 7500), MainHTTPHandler)
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    # logging.info("Starting server at %s" % 7500)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
