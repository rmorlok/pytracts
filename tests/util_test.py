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

"""Tests for pytracts.util."""
from tests import test_util

__author__ = 'rafek@google.com (Rafe Kaplan)'

import datetime
import random
import sys
import unittest
import types

from pytracts import util


if sys.version_info >= (3, 0, 0):
    unicode = str
    basestring = str
    long = int

    def cmp(a, b):
        return (a > b) - (a < b)


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):
    MODULE = util


class PadStringTest(test_util.TestCase):
    def testPadEmptyString(self):
        self.assertEqual(' ' * 512, util.pad_string(''))

    def testPadString(self):
        self.assertEqual('hello' + (507 * ' '), util.pad_string('hello'))

    def testPadLongString(self):
        self.assertEqual('x' * 1000, util.pad_string('x' * 1000))


class UtilTest(test_util.TestCase):
    def testDecoratedFunction_LengthZero(self):
        @util.positional(0)
        def fn(kwonly=1):
            return [kwonly]

        self.assertEqual([1], fn())
        self.assertEqual([2], fn(kwonly=2))
        self.assertRaisesWithRegexpMatch(TypeError,
                                         r'fn\(\) takes at most 0 positional '
                                         r'arguments \(1 given\)',
                                         fn, 1)

    def testDecoratedFunction_LengthOne(self):
        @util.positional(1)
        def fn(pos, kwonly=1):
            return [pos, kwonly]

        self.assertEqual([1, 1], fn(1))
        self.assertEqual([2, 2], fn(2, kwonly=2))
        self.assertRaisesWithRegexpMatch(TypeError,
                                         r'fn\(\) takes at most 1 positional '
                                         r'argument \(2 given\)',
                                         fn, 2, 3)

    def testDecoratedFunction_LengthTwoWithDefault(self):
        @util.positional(2)
        def fn(pos1, pos2=1, kwonly=1):
            return [pos1, pos2, kwonly]

        self.assertEqual([1, 1, 1], fn(1))
        self.assertEqual([2, 2, 1], fn(2, 2))
        self.assertEqual([2, 3, 4], fn(2, 3, kwonly=4))
        self.assertRaisesWithRegexpMatch(TypeError,
                                         r'fn\(\) takes at most 2 positional '
                                         r'arguments \(3 given\)',
                                         fn, 2, 3, 4)

    def testDecoratedMethod(self):
        class MyClass(object):
            @util.positional(2)
            def meth(self, pos1, kwonly=1):
                return [pos1, kwonly]

        self.assertEqual([1, 1], MyClass().meth(1))
        self.assertEqual([2, 2], MyClass().meth(2, kwonly=2))
        self.assertRaisesWithRegexpMatch(TypeError,
                                         r'meth\(\) takes at most 2 positional '
                                         r'arguments \(3 given\)',
                                         MyClass().meth, 2, 3)


class AcceptItemTest(test_util.TestCase):
    def CheckAttributes(self, item, main_type, sub_type, q=1, values={}, index=1):
        self.assertEqual(index, item.index)
        self.assertEqual(main_type, item.main_type)
        self.assertEqual(sub_type, item.sub_type)
        self.assertEqual(q, item.q)
        self.assertEqual(values, item.values)

    def testParse(self):
        self.CheckAttributes(util.AcceptItem('*/*', 1), None, None)
        self.CheckAttributes(util.AcceptItem('text/*', 1), 'text', None)
        self.CheckAttributes(util.AcceptItem('text/plain', 1), 'text', 'plain')
        self.CheckAttributes(
            util.AcceptItem('text/plain; q=0.3', 1), 'text', 'plain', 0.3,
            values={'q': '0.3'})
        self.CheckAttributes(
            util.AcceptItem('text/plain; level=2', 1), 'text', 'plain',
            values={'level': '2'})
        self.CheckAttributes(
            util.AcceptItem('text/plain', 10), 'text', 'plain', index=10)

    def testCaseInsensitive(self):
        self.CheckAttributes(util.AcceptItem('Text/Plain', 1), 'text', 'plain')

    def testBadValue(self):
        self.assertRaises(util.AcceptError,
                          util.AcceptItem, 'bad value', 1)
        self.assertRaises(util.AcceptError,
                          util.AcceptItem, 'bad value/', 1)
        self.assertRaises(util.AcceptError,
                          util.AcceptItem, '/bad value', 1)

    def testSortKey(self):
        item = util.AcceptItem('main/sub; q=0.2; level=3', 11)
        self.assertEqual((False, False, -0.2, False, 11), item.sort_key)

        item = util.AcceptItem('main/*', 12)
        self.assertEqual((False, True, -1, True, 12), item.sort_key)

        item = util.AcceptItem('*/*', 1)
        self.assertEqual((True, True, -1, True, 1), item.sort_key)

    def testSort(self):
        i1 = util.AcceptItem('text/*', 1)
        i2 = util.AcceptItem('text/html', 2)
        i3 = util.AcceptItem('text/html; q=0.9', 3)
        i4 = util.AcceptItem('text/html; q=0.3', 4)
        i5 = util.AcceptItem('text/xml', 5)
        i6 = util.AcceptItem('text/html; level=1', 6)
        i7 = util.AcceptItem('*/*', 7)
        items = [i1, i2, i3, i4, i5, i6, i7]
        random.shuffle(items)
        self.assertEqual([i6, i2, i5, i3, i4, i1, i7], sorted(items))

    def testMatchAll(self):
        item = util.AcceptItem('*/*', 1)
        self.assertTrue(item.match('text/html'))
        self.assertTrue(item.match('text/plain; level=1'))
        self.assertTrue(item.match('image/png'))
        self.assertTrue(item.match('image/png; q=0.3'))

    def testMatchMainType(self):
        item = util.AcceptItem('text/*', 1)
        self.assertTrue(item.match('text/html'))
        self.assertTrue(item.match('text/plain; level=1'))
        self.assertFalse(item.match('image/png'))
        self.assertFalse(item.match('image/png; q=0.3'))

    def testMatchFullType(self):
        item = util.AcceptItem('text/plain', 1)
        self.assertFalse(item.match('text/html'))
        self.assertTrue(item.match('text/plain; level=1'))
        self.assertFalse(item.match('image/png'))
        self.assertFalse(item.match('image/png; q=0.3'))

    def testMatchCaseInsensitive(self):
        item = util.AcceptItem('text/plain', 1)
        self.assertTrue(item.match('tExt/pLain'))

    def testStr(self):
        self.assertHeaderSame('*/*', str(util.AcceptItem('*/*', 1)))
        self.assertHeaderSame('text/*', str(util.AcceptItem('text/*', 1)))
        self.assertHeaderSame('text/plain',
                              str(util.AcceptItem('text/plain', 1)))
        self.assertHeaderSame('text/plain; q=0.2',
                              str(util.AcceptItem('text/plain; q=0.2', 1)))
        self.assertHeaderSame(
            'text/plain; q=0.2; level=1',
            str(util.AcceptItem('text/plain; level=1; q=0.2', 1)))

    def testRepr(self):
        self.assertEqual("AcceptItem('*/*', 1)", repr(util.AcceptItem('*/*', 1)))
        self.assertEqual("AcceptItem('text/plain', 11)",
                          repr(util.AcceptItem('text/plain', 11)))

    def testValues(self):
        item = util.AcceptItem('text/plain; a=1; b=2; c=3;', 1)
        values = item.values
        self.assertEqual(dict(a="1", b="2", c="3"), values)
        values['a'] = "7"
        self.assertNotEqual(values, item.values)


class ParseAcceptHeaderTest(test_util.TestCase):
    def testIndex(self):
        accept_header = """text/*, text/html, text/html; q=0.9,
                       text/xml,
                       text/html; level=1, */*"""
        accepts = util.parse_accept_header(accept_header)
        self.assertEqual(6, len(accepts))
        self.assertEqual([4, 1, 3, 2, 0, 5], [a.index for a in accepts])


class ChooseContentTypeTest(test_util.TestCase):
    def testIgnoreUnrequested(self):
        self.assertEqual('application/json',
                          util.choose_content_type(
                              'text/plain, application/json, */*',
                              ['application/X-Google-protobuf',
                               'application/json'
                              ]))

    def testUseCorrectPreferenceIndex(self):
        self.assertEqual('application/json',
                          util.choose_content_type(
                              '*/*, text/plain, application/json',
                              ['application/X-Google-protobuf',
                               'application/json'
                              ]))

    def testPreferFirstInList(self):
        self.assertEqual('application/X-Google-protobuf',
                          util.choose_content_type(
                              '*/*',
                              ['application/X-Google-protobuf',
                               'application/json'
                              ]))

    def testCaseInsensitive(self):
        self.assertEqual('application/X-Google-protobuf',
                          util.choose_content_type(
                              'application/x-google-protobuf',
                              ['application/X-Google-protobuf',
                               'application/json'
                              ]))


class GetPackageForModuleTest(test_util.TestCase):
    def setUp(self):
        self.original_modules = dict(sys.modules)

    def tearDown(self):
        sys.modules.clear()
        sys.modules.update(self.original_modules)

    def CreateModule(self, name, file_name=None):
        if file_name is None:
            file_name = '%s.py' % name
        module = types.ModuleType(name)
        sys.modules[name] = module
        return module

    def assertPackageEquals(self, expected, actual):
        self.assertEqual(expected, actual)
        if actual is not None:
            self.assertTrue(isinstance(actual, unicode))

    def testByString(self):
        module = self.CreateModule('service_module')
        module.package = 'my_package'
        self.assertPackageEquals('my_package',
                                 util.get_package_for_module('service_module'))

    def testModuleNameNotInSys(self):
        self.assertPackageEquals(None,
                                 util.get_package_for_module('service_module'))

    def testHasPackage(self):
        module = self.CreateModule('service_module')
        module.package = 'my_package'
        self.assertPackageEquals('my_package', util.get_package_for_module(module))

    def testHasModuleName(self):
        module = self.CreateModule('service_module')
        self.assertPackageEquals('service_module',
                                 util.get_package_for_module(module))

    def testIsMain(self):
        module = self.CreateModule('__main__')
        module.__file__ = '/bing/blam/bloom/blarm/my_file.py'
        self.assertPackageEquals('my_file', util.get_package_for_module(module))

    def testIsMainCompiled(self):
        module = self.CreateModule('__main__')
        module.__file__ = '/bing/blam/bloom/blarm/my_file.pyc'
        self.assertPackageEquals('my_file', util.get_package_for_module(module))

    def testNoExtension(self):
        module = self.CreateModule('__main__')
        module.__file__ = '/bing/blam/bloom/blarm/my_file'
        self.assertPackageEquals('my_file', util.get_package_for_module(module))

    def testNoPackageAtAll(self):
        module = self.CreateModule('__main__')
        self.assertPackageEquals('__main__', util.get_package_for_module(module))


class DateTimeTests(test_util.TestCase):
    def testDecodeDateTime(self):
        """Test that a RFC 3339 datetime string is decoded properly."""
        for datetime_string, datetime_vals in (
                ('2012-09-30T15:31:50.262', (2012, 9, 30, 15, 31, 50, 262000)),
                ('2012-09-30T15:31:50', (2012, 9, 30, 15, 31, 50, 0))):
            decoded = util.decode_datetime(datetime_string)
            expected = datetime.datetime(*datetime_vals)
            self.assertEqual(expected, decoded)

    def testDateTimeTimeZones(self):
        """Test that a datetime string with a timezone is decoded correctly."""
        for datetime_string, datetime_vals in (
                ('2012-09-30T15:31:50.262-06:00',
                 (2012, 9, 30, 15, 31, 50, 262000, util.TimeZoneOffset(-360))),
                ('2012-09-30T15:31:50.262+01:30',
                 (2012, 9, 30, 15, 31, 50, 262000, util.TimeZoneOffset(90))),
                ('2012-09-30T15:31:50+00:05',
                 (2012, 9, 30, 15, 31, 50, 0, util.TimeZoneOffset(5))),
                ('2012-09-30T15:31:50+00:00',
                 (2012, 9, 30, 15, 31, 50, 0, util.TimeZoneOffset(0))),
                ('2012-09-30t15:31:50-00:00',
                 (2012, 9, 30, 15, 31, 50, 0, util.TimeZoneOffset(0))),
                ('2012-09-30t15:31:50z',
                 (2012, 9, 30, 15, 31, 50, 0, util.TimeZoneOffset(0))),
                ('2012-09-30T15:31:50-23:00',
                 (2012, 9, 30, 15, 31, 50, 0, util.TimeZoneOffset(-1380)))):
            decoded = util.decode_datetime(datetime_string)
            expected = datetime.datetime(*datetime_vals)
            self.assertEqual(expected, decoded)

    def testDecodeDateTimeInvalid(self):
        """Test that decoding malformed datetime strings raises execptions."""
        for datetime_string in ('invalid',
                                '2012-09-30T15:31:50.',
                                '-08:00 2012-09-30T15:31:50.262',
                                '2012-09-30T15:31',
                                '2012-09-30T15:31Z',
                                '2012-09-30T15:31:50ZZ',
                                '2012-09-30T15:31:50.262 blah blah -08:00',
                                '1000-99-99T25:99:99.999-99:99'):
            self.assertRaises(ValueError, util.decode_datetime, datetime_string)

    def testTimeZoneOffsetDelta(self):
        """Test that delta works with TimeZoneOffset."""
        time_zone = util.TimeZoneOffset(datetime.timedelta(minutes=3))
        epoch = time_zone.utcoffset(datetime.datetime.utcfromtimestamp(0))
        self.assertEqual(10800, epoch.total_seconds())


def main():
    unittest.main()


if __name__ == '__main__':
    main()
