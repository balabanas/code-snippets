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
    """Metaclass, implementing methods to pull attributes name out of instances during validation,
    and also method for basic validation of `required` and `nullable` properties"""
    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    def __set_name__(self, owner, name):
        self.name = '_' + name

    def __get__(self, instance, owner):
        return getattr(instance, self.name)

    # @staticmethod
    # def _get_name(instance, field):
    #     for k, v in type(instance).__dict__.items():
    #         if v is field:
    #             return k

    @staticmethod
    def validate_nullable(field, value):
        if not field.nullable and value is None:
            raise TypeError(f"Field {field.name[1:]} is not nullable. Got: {value}")


class CharField(BaseField):
    """Storage for general char arguments, with validating descriptor"""
    def __set__(self, instance, value):
        self.validate_nullable(self, value)
        ornone = " or None" if self.nullable else ''
        if not isinstance(value, str) and value is not None:
            raise TypeError(f"Field {self.name[1:]} expects string{ornone}. Got: {value}")
        setattr(instance, self.name, value)


class ArgumentsField(BaseField):
    """Storage for arguments dict, with validating descriptor"""
    def __set__(self, instance, value):
        self.validate_nullable(self, value)
        setattr(instance, self.name, value)


class EmailField(CharField):
    """Storage for email argument, with validating descriptor"""
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value is not None:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(pattern, value) is None:
                raise TypeError(f"Field {self.name[1:]} dose not meet e-mail format")
        # setattr(instance, self.name, value)


class PhoneField(BaseField):
    """Storage for phone argument, with validating descriptor"""
    def __set__(self, instance, value):
        # super().__set__(instance, value)
        self.validate_nullable(self, value)
        if value:  # value was already set by super method, take it
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
                date = datetime.datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                raise TypeError(
                    f"Field {self.name[1:]} should be str formatted as dd.mm.yyyy"
                )
        setattr(instance, self.name, date)


class BirthDayField(DateField):
    """Storage for birthday argument, with validating descriptor"""
    def __set__(self, instance, value):
        super().__set__(instance, value)
        date = getattr(instance, self.name)  # value was already set by super method, take it
        if date:
            age = datetime.datetime.today() - date
            if age > datetime.timedelta(days=365 * 70):
                raise TypeError(f"Field {self.name[1:]} should be < 70 years behind current date. Got: {date}")


class GenderField(BaseField):
    """Storage for gender argument, with validating descriptor"""
    def __set__(self, instance, value):
        self.validate_nullable(self, value)
        if value and not isinstance(value, (int, float)):
            raise TypeError(f"If specified, field {self.name[1:]} should be a number")
        ornone = " or None" if self.nullable else ''
        # if not isinstance(value, int) and value is not None:
        #     raise TypeError(f"Field {self._get_name(instance, self)} expects int{ornone}. Got: {value}")
        if value not in [0, 1, 2]:
            raise TypeError(f"Field {self.name[1:]} expects int values of {ornone}. Got: {value}")
        # pass
        setattr(instance, self.name, value)


class ClientIDsField(BaseField):
    """Storage for client IDs list, with validating descriptor"""
    def __set__(self, instance, value):
        self.validate_nullable(self, value)
        ornone = " or None" if self.nullable else ''
        if not isinstance(value, list) and value is not None:
            raise TypeError(f"Field {self.name[1:]} expects list{ornone}. Got: {value}")
        elif isinstance(value, list):
            if len(value) == 0:
                raise TypeError(f"Field {self.name[1:]} expects non-empty list. Got: {value}")
        if value:
            for el in value:
                if not isinstance(el, int):
                    raise TypeError(f"Field {self.name[1:]} expects ints in a list. Got: {value}")
        setattr(instance, self.name, value)


class CollectFieldsMeta(type):
    """Collects *Field-class attributes of a Class, as defined in `field_classes`,
    into a list, available as an attribute of a Class instance. Affords easy iteration over
    attributes (in fact, Fields excpected in a request, which might differ from Class to a Class)"""
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

    def __init__(self, request, ctx, store):
        self.response: Union[str, dict] = {}
        self.code: int = OK
        self.request = request
        self.ctx = ctx
        self.store = store

    def validate_required(self):
        for f in self.request_fields:
            if self.__class__.__dict__[f].required:
                try:
                    getattr(self, f'_{f}')
                except AttributeError:
                    self.response = f"Field {f} is required!"
                    self.code = INVALID_REQUEST
                    raise False
        return True


class ClientsInterestsRequest(BaseRequest):
    """Defines clients-interests scoring arguments, parses argument's dictionary and assign values,
        implements methods to validate fields, call scoring function and return response"""

    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def _validate_params(self):
        try:
            body = self.request['body']
            for attr_name in self.request_fields:
                if 'arguments' in body and attr_name in body['arguments']:
                    setattr(self, attr_name, body['arguments'][attr_name])
            self.validate_required()  # after setting attributes, let's check if all required were set
        except TypeError as e:
            self.response = e.args[0]
            self.code = INVALID_REQUEST
            return False

        if self.client_ids is None:
            self.response = "No valid client_ids were requested"
            self.code = INVALID_REQUEST
            return False
        return True

    def process_request(self):
        if self._validate_params():
            self.response = {f'{i}': get_interests(1, i) for i in self.client_ids}
            self.ctx['nclients'] = len(self.client_ids)
            self.code = OK
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

    def _validate_params(self):
        try:
            body = self.request['body']
            for attr_name in self.request_fields:
                if 'arguments' in body and attr_name in body['arguments']:
                    setattr(self, attr_name, body['arguments'][attr_name])
            self.validate_required()  # after setting attributes, let's check if all required were set
        except TypeError as e:
            self.response = e.args[0]
            self.code = INVALID_REQUEST
            return False
        if not (all(f'_{f}' in self.__dict__ for f in ('phone', 'email'))
                or all(f'_{f}' in self.__dict__ for f in ('first_name', 'last_name'))
                or all(f'_{f}' in self.__dict__ for f in ('gender', 'birthday'))):
            self.response = "No valid pair of arguments found"
            self.code = INVALID_REQUEST
            return False
        return True

    def process_request(self):
        if self._validate_params():
            request_fields_vals = {f: getattr(self, f) if f'_{f}' in self.__dict__ else None for f in
                                   self.request_fields}
            print(request_fields_vals)
            score = get_score(self.store, **request_fields_vals)
            self.response = {'score': score}
            self.ctx['has'] = [f for f in self.request_fields if f'_{f}' in self.__dict__]
            self.code = OK
        return self.response, self.code


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
        self.response = "Forbidden"
        self.code = FORBIDDEN
        return False

    def _validate_params(self):
        try:
            body = self.request['body']
            for attr_name in self.request_fields:
                if attr_name in body:
                    setattr(self, attr_name, body[attr_name])
            self.validate_required()
        except TypeError as e:
            self.response = e.args[0]
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
    parser.add_argument('-p', '--port', type=int, default=8080, help="Port to run the API on")
    parser.add_argument('-l', '--log', type=str, default='log.txt', help="Path to a log file")
    args: argparse.Namespace = parser.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
