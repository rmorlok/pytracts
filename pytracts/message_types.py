#!/usr/bin/env python
#
# Copyright 2014 Docalytics Inc, Copyright 2010 Google Inc.
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

"""Simple protocol message types.

Includes new message and field types that are outside what is defined by the
protocol buffers standard.
"""

__author__ = 'rafek@google.com (Rafe Kaplan)'

import datetime

from . import messages
from . import util

__all__ = [
    'VoidMessage',
    'ErrorMessage',
    'error_message_from_exception'
]


class VoidMessage(messages.Message):
    """Empty message."""


class ErrorMessage(messages.Message):
    """
    A message to accompany errors.
    """
    title = messages.StringField()
    message = messages.StringField()
    explanation = messages.StringField()


def error_message_from_exception(exception):
    """
    Create an instance from an exception object.

    :param exception: the exception

    :return: ErrorMessage
    """
    result = ErrorMessage()

    if hasattr(exception, 'message'):
        result.message = exception.message
    elif hasattr(exception, 'description'):
        result.message = exception.description

    if hasattr(exception, 'title'):
        result.title = exception.title
    elif hasattr(exception, 'name'):
        result.title = exception.name

    if hasattr(exception, 'explanation'):
        result.explanation = exception.explanation

    if hasattr(exception, 'detail'):
        result.message = exception.detail

    return result
