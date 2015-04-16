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

if __name__ == '__main__':
    unittest.main()
