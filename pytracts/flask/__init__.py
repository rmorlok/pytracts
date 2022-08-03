#!/usr/bin/env python
#
# Copyright 2011 Google Inc.
# Copyright 2015 Docalytics Inc.
# Copyright 2022 Morlok Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Main module for pytracts package."""

__author__ = 'Ryan Morlok (ryan.morlok@morlok.com)'

import sys
import logging
import json

from flask import request, make_response

from pytracts import to_json, messages, to_url, message_types, util, query, exceptions

__ALL__ = [
    'messages',
    'message_types',
    'log_headers',
    'endpoint',
    'query'
]


if sys.version_info >= (3, 0, 0):
    unicode = str
    basestring = str
    long = int

    def cmp(a, b):
        return (a > b) - (a < b)


def log_headers(f):
    """
    Annotation used to log the HTTP headers of a request. Used for debugging. Headers will be logged as info.

    :return: wrapper function performing the requested operation
    """
    def wrapper(*args, **kwargs):
        import logging

        for header_key, header_value in request.headers.items():
            logging.info(header_key + ": " + header_value)

        # Call the underlying function with the parameter added
        return f(*args, **kwargs)

    return wrapper


# List of all endpoints that have been registered using the endpoint decorator. This still requires
# the modules be imported appropriately before anything is done with this data
_ALL_ENDPOINTS = []


def register_endpoints(app):
    """
    Register all endpoints that have been annotated with the @endpoint decorator with a flask app.
    To be registered, these modules must have been imported previously to this call.

    :param app: the flask app to register with
    """
    for endpoint_def in sorted(_ALL_ENDPOINTS, key=lambda ed: ed.get('rule', '')):
        app.add_url_rule(**endpoint_def)


def endpoint(route, methods=None, query=None, body=None, lenient=False, defaults=None, subdomain=None):
    """
    Decorator that allows an endpoint to use pytracts messages for the request and response.

    :param route: the string for the route e.g. /foo/bar
    :param methods: list of methods supported, e.g. ['GET', 'POST']
    :param query: dict of parameter-name/message-type pairs for messages to be decoded from the query string
    :param body: dict of parameter-name/messaage-type pairs for messages to be decoded from the JSON body
    :param lenient: should an exception be thrown if the request content type is not JSON?
    :param defaults: defaults passed to flask to create route
    :param subdomain: subdomain passed to flask to create route
    """
    for name, message_type in (body or {}).items():
        if not isinstance(message_type, messages._MessageClass):
            raise TypeError("Body '{}' must be of type pytracts.messages.Message".format(name))

    for name, message_type in (query or {}).items():
        if not isinstance(message_type, messages._MessageClass):
            raise TypeError("Query '{}' must be of type pytracts.messages.Message".format(name))

    def get_wrapper(route, methods, query, body, lenient, defaults, subdomain, f):
        def wrapper(*args, **kwargs):
            try:
                pj = to_json.JsonEncoder()

                # If we have a body message provided, this request must be json
                if body is not None:
                    request_content_type = request.headers.get('Content-Type', None)

                    if request_content_type is not None:
                        request_content_type = request_content_type.lower().split(";")[0]

                    if request_content_type != "application/json" and not lenient:
                        raise exceptions.HTTPUnsupportedMediaType(
                            "Content type must be 'application/json'")

                for name, message_type in (query or {}).items():
                    try:
                        query_string = request.url[len(request.base_url) + 1:] if len(
                            request.url) > len(request.base_url) + 1 else ''
                        m = to_url.decode_message(message_type, query_string)
                        kwargs[name] = m

                    except (ValueError, messages.Error) as error:
                        raise exceptions.HTTPBadRequest(
                            error.message or "Request JSON is invalid.")

                for name, message_type in (body or {}).items():
                    try:
                        m = pj.decode_message(message_type, request.get_data(as_text=True))
                        kwargs[name] = m

                    except ValueError:
                        raise exceptions.HTTPBadRequest("Request body is invalid.")
                    except messages.Error as error:
                        raise exceptions.HTTPBadRequest(str(error))

                # Everything is good. Call the actual handler method
                result = f(*args, **kwargs)

                response_code = None
                headers = {}
            except Exception as e:
                result = message_types.error_message_from_exception(e)

                headers = {}
                response_code = 500

                if hasattr(e, 'code'):
                    response_code = e.code

                # Log only errors
                if response_code < 200 or response_code > 404:
                    logging.exception(e)

            if type(result) != tuple:
                result = (result,)

            response = make_response()

            for val in result:
                if type(val) == int:
                    response_code = val
                elif type(val) == dict:
                    headers.update(val)
                elif isinstance(val, messages.Message):
                    response_code = response_code or 200
                    response.content_type = 'application/json'
                    response.set_data(pj.encode_message(val))

            if response_code:
                response.status_code = response_code

            for k, v in headers.items():
                response.headers[k] = v

            return response

        epd = {
            'rule': route,
            'endpoint': f.__name__,
            'view_func': wrapper,
            'methods': methods
        }

        if defaults is not None:
            epd['defaults'] = defaults

        if subdomain is not None:
            epd['subdomain'] = subdomain

        _ALL_ENDPOINTS.append(epd)

        return wrapper

    return util.curry(get_wrapper, route, methods, query, body, lenient, defaults, subdomain)
