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

from uuid import uuid4

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
    def wrapper(fself, *arguments, **keywords):
        import logging

        for header_key, header_value in fself.request.headers.items():
            logging.info(header_key + ": " + header_value)

        # Call the underlying function with the parameter added
        return f(fself, *arguments, **keywords)

    return wrapper


def endpoint(_wrapped_function=None, lenient=False, **kwargs):
    """
    Decorator that allows an endpoint to use pytracts messages for the request and response.
    """

    if len(kwargs) > 1:
        raise IndexError("Cannot have more than one mapping for request body")

    if len(kwargs) == 1:
        body_param_name = list(kwargs.keys())[0]
        body_param_type = list(kwargs.values())[0]

        if not isinstance(body_param_type, messages._MessageClass):
            raise TypeError("Body must be of type pytracts.messages.Message")
    else:
        body_param_name = None
        body_param_type = None

    def get_wrapper(body_param_name, body_param_type, lenient, f):
        def wrapper(self, *arguments, **keywords):
            pj = to_json.JsonEncoder()

            # If we have a body message provided, this request must be json
            if body_param_name:
                request_content_type = self.request.content_type

                if request_content_type is not None:
                    request_content_type = request_content_type.lower().split(";")[0]

                if request_content_type != "application/json" and not lenient:
                    raise exceptions.HTTPUnsupportedMediaType("Content type must be 'application/json'")

                try:
                    m = pj.decode_message(body_param_type, self.request.body)
                    keywords[body_param_name] = m

                except (ValueError, messages.Error) as error:
                    raise exceptions.HTTPBadRequest(error.message or "Request body JSON is invalid.")

            try:
                # Everything is good. Call the actual handler method
                result = f(self, *arguments, **keywords)

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

            for val in result:
                if type(val) == int:
                    response_code = val
                elif type(val) == dict:
                    headers.update(val)
                elif isinstance(val, messages.Message):
                    response_code = response_code or 200
                    self.response.content_type = 'application/json'
                    self.response.write(pj.encode_message(val))

            if response_code:
                self.response.status_int = response_code

            for k, v in headers.items():
                self.response.headers[k] = v

        return wrapper

    if _wrapped_function is not None and hasattr(_wrapped_function, '__call__'):
        return get_wrapper(body_param_name=body_param_name, body_param_type=body_param_type, lenient=lenient, f=_wrapped_function)
    else:
        return util.curry(get_wrapper, body_param_name, body_param_type, lenient)