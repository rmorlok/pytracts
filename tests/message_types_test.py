#!/usr/bin/env python
#
# Copyright 2014 Docalytics Inc, Copyright 2013 Google Inc.
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

"""Tests for pytracts.message_types."""
from tests import test_util

__author__ = 'rafek@google.com (Rafe Kaplan)'

import datetime

import unittest

from pytracts import message_types
from pytracts import messages
from pytracts import util


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):
    MODULE = message_types


class DateTimeFieldTest(test_util.TestCase):
    def test_value_to_message(self):
        field = message_types.DateTimeField()
        message = field.value_to_message(datetime.datetime(2033, 2, 4, 11, 22, 10))
        self.assertEqual(message_types.DateTimeMessage(milliseconds=1991128930000),
                         message)

    def test_value_to_message_bad_value(self):
        field = message_types.DateTimeField()
        self.assertRaisesWithRegexpMatch(
            messages.EncodeError,
            'Expected type datetime, got int: 20',
            field.value_to_message, 20)

    def test_value_to_message_with_time_zone(self):
        time_zone = util.TimeZoneOffset(60 * 10)
        field = message_types.DateTimeField()
        message = field.value_to_message(
            datetime.datetime(2033, 2, 4, 11, 22, 10, tzinfo=time_zone))
        self.assertEqual(message_types.DateTimeMessage(milliseconds=1991128930000,
                                                       time_zone_offset=600),
                         message)

    def test_value_from_message(self):
        message = message_types.DateTimeMessage(milliseconds=1991128000000)
        field = message_types.DateTimeField()
        timestamp = field.value_from_message(message)
        self.assertEqual(datetime.datetime(2033, 2, 4, 11, 6, 40),
                         timestamp)

    def test_value_from_message_bad_value(self):
        field = message_types.DateTimeField()
        self.assertRaisesWithRegexpMatch(
            messages.DecodeError,
            'Expected type DateTimeMessage, got VoidMessage: <VoidMessage>',
            field.value_from_message, message_types.VoidMessage())

    def test_value_from_message_with_time_zone(self):
        message = message_types.DateTimeMessage(milliseconds=1991128000000,
                                                time_zone_offset=300)
        field = message_types.DateTimeField()
        timestamp = field.value_from_message(message)
        time_zone = util.TimeZoneOffset(60 * 5)
        self.assertEqual(datetime.datetime(2033, 2, 4, 11, 6, 40, tzinfo=time_zone),
                         timestamp)


if __name__ == '__main__':
    unittest.main()
