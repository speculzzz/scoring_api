#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import logging
import uuid
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer

import fields
from scoring import get_interests, get_score

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


class ClientsInterestsRequest(object):
    client_ids = fields.ClientIDsField(required=True)
    date = fields.DateField(required=False, nullable=True)

    def __init__(self, client_ids=None, date=None):
        self.client_ids = client_ids
        self.date = date

    @classmethod
    def from_arguments(cls, arguments):
        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary")

        return cls(
            client_ids=arguments.get("client_ids"),
            date=arguments.get("date")
        )

    def is_valid_request(self):
        return True


class OnlineScoreRequest(object):
    first_name = fields.CharField(required=False, nullable=True)
    last_name = fields.CharField(required=False, nullable=True)
    email = fields.EmailField(required=False, nullable=True)
    phone = fields.PhoneField(required=False, nullable=True)
    birthday = fields.BirthDayField(required=False, nullable=True)
    gender = fields.GenderField(required=False, nullable=True)

    def __init__(self, first_name=None, last_name=None, email=None, phone=None, birthday=None, gender=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.birthday = birthday
        self.gender = gender

    @classmethod
    def from_arguments(cls, arguments):
        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary")

        return cls(
            first_name=arguments.get("first_name"),
            last_name=arguments.get("last_name"),
            email=arguments.get("email"),
            phone=arguments.get("phone"),
            birthday=arguments.get("birthday"),
            gender=arguments.get("gender"),
        )

    def is_valid_request(self):
        return (
            (self.phone and self.email)
            or (self.first_name and self.last_name)
            or (self.gender is not None and self.birthday)
        )


REQUEST_METHOD_MAPPING = {
    "clients_interests": ClientsInterestsRequest,
    "online_score": OnlineScoreRequest,
}


class MethodRequest(object):
    account = fields.CharField(required=False, nullable=True)
    login = fields.CharField(required=True, nullable=True)
    token = fields.CharField(required=True, nullable=True)
    arguments = fields.ArgumentsField(required=True, nullable=True)
    method = fields.CharField(required=True, nullable=False)

    def __init__(self, account=None, login=None, token=None, arguments=None, method=None):
        self.account = account
        self.login = login
        self.token = token
        self.arguments = arguments
        self.method = method

    @classmethod
    def from_request(cls, request):
        if not isinstance(request, dict):
            raise ValueError("Request data must be a dictionary")

        return cls(
            account=request.get("account"),
            login=request.get("login"),
            token=request.get("token"),
            arguments=request.get("arguments"),
            method=request.get("method")
        )

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(
            (datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode("utf-8")
        ).hexdigest()
    else:
        digest = hashlib.sha512(
            (request.account + request.login + SALT).encode("utf-8")
        ).hexdigest()
    return digest == request.token


def method_handler(request, ctx, store):
    response, code = None, None

    try:
        # Extract the request body
        request_body = request.get("body")
        if not request_body:
            raise ValueError("Request must contain a 'body'")

        method_request = MethodRequest.from_request(request_body)

        if not check_auth(method_request):
            code = FORBIDDEN
            logging.error(f"{method_request.account}/{method_request.login} access "
                          f"to {method_request.method} is prohibited")

        elif method_request.method in REQUEST_METHOD_MAPPING.keys():
            method = REQUEST_METHOD_MAPPING[method_request.method].from_arguments(method_request.arguments)
            if not method.is_valid_request():
                raise ValueError("Invalid request")

            if isinstance(method, OnlineScoreRequest):
                logging.info("Got the 'online_score' request")

                ctx["has"] = []
                for key, val in method_request.arguments.items():
                    if isinstance(val, (str, list)) and not val:
                        continue
                    ctx["has"].append(key)

                score = get_score(
                    store=store,
                    first_name=method.first_name,
                    last_name=method.last_name,
                    email=method.email,
                    phone=method.phone,
                    birthday=method.birthday,
                    gender=method.gender,
                )
                code = OK
                response = {"score": int(ADMIN_SALT) if method_request.is_admin else score}

            elif isinstance(method, ClientsInterestsRequest):
                logging.info("Got the 'clients_interests' request")

                response = {}
                nclients = 0
                for cid in method.client_ids:
                    response[str(cid)] = get_interests(store, cid)
                    nclients += 1
                ctx["nclients"] = nclients
                code = OK

            else:
                raise ValueError("Unknown method")

    except ValueError as e:
        code = INVALID_REQUEST
        response = str(e.args[0])

    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store = None

    def get_request_id(self, headers):
        return headers.get("HTTP_X_REQUEST_ID", uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers["Content-Length"]))
            request = json.loads(data_string)
        except Exception:
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
        self.wfile.write(json.dumps(r).encode("utf-8"))
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )

    server = HTTPServer(("localhost", args.port), MainHTTPHandler)

    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
