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

"""Tests for pytracts.to_url."""
from tests import test_util

__author__ = 'rafek@google.com (Rafe Kaplan)'

try:
    from urlparse import urlparse, parse_qs, urlencode
except ImportError:
    from urllib.parse import urlparse, parse_qs, urlencode


import unittest
import urllib
from datetime import datetime

from pytracts import message_types
from pytracts import messages
from pytracts import to_url


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):
    MODULE = to_url


class SuperMessage(messages.Message):
    """A test message with a nested message field."""

    sub_message = messages.MessageField(test_util.OptionalMessage)
    sub_messages = messages.MessageField(test_util.OptionalMessage, repeated=True)


class SuperSuperMessage(messages.Message):
    """A test message with two levels of nested."""

    sub_message = messages.MessageField(SuperMessage)
    sub_messages = messages.MessageField(SuperMessage, repeated=True)


class URLEncodedRequestBuilderTest(test_util.TestCase):
    """Test the URL Encoded request builder."""

    def testMakePath(self):
        builder = to_url.URLEncodedRequestBuilder(SuperSuperMessage(), prefix='pre.')

        self.assertEqual(None, builder.make_path(''))
        self.assertEqual(None, builder.make_path('no_such_field'))
        self.assertEqual(None, builder.make_path('pre.no_such_field'))

        # Missing prefix.
        self.assertEqual(None, builder.make_path('sub_message'))

        # Valid parameters.
        self.assertEqual((('sub_message', None),),
                          builder.make_path('pre.sub_message'))
        self.assertEqual((('sub_message', None), ('sub_messages', 1)),
                          builder.make_path('pre.sub_message.sub_messages-1'))
        self.assertEqual(
            (('sub_message', None),
             ('sub_messages', 1),
             ('int64_value', None)),
            builder.make_path('pre.sub_message.sub_messages-1.int64_value'))

        # Missing index.
        self.assertEqual(
            None,
            builder.make_path('pre.sub_message.sub_messages.integer_field'))

        # Has unexpected index.
        self.assertEqual(
            None,
            builder.make_path('pre.sub_message.sub_message-1.integer_field'))

    def testAddParameter_SimpleAttributes(self):
        message = test_util.OptionalMessage()
        builder = to_url.URLEncodedRequestBuilder(message, prefix='pre.')

        self.assertTrue(builder.add_parameter('pre.int64_value', ['10']))
        self.assertTrue(builder.add_parameter('pre.string_value', ['a string']))
        self.assertTrue(builder.add_parameter('pre.enum_value', ['VAL1']))
        self.assertEqual(10, message.int64_value)
        self.assertEqual('a string', message.string_value)
        self.assertEqual(test_util.OptionalMessage.SimpleEnum.VAL1,
                          message.enum_value)

    def testAddParameter_InvalidAttributes(self):
        message = SuperSuperMessage()
        builder = to_url.URLEncodedRequestBuilder(message, prefix='pre.')

        def assert_empty():
            self.assertEqual(None, getattr(message, 'sub_message'))
            self.assertEqual([], getattr(message, 'sub_messages'))

        self.assertFalse(builder.add_parameter('pre.nothing', ['x']))
        assert_empty()

        self.assertFalse(builder.add_parameter('pre.sub_messages', ['x']))
        self.assertFalse(builder.add_parameter('pre.sub_messages-1.nothing', ['x']))
        assert_empty()

    def testAddParameter_NestedAttributes(self):
        message = SuperSuperMessage()
        builder = to_url.URLEncodedRequestBuilder(message, prefix='pre.')

        # Set an empty message fields.
        self.assertTrue(builder.add_parameter('pre.sub_message', ['']))
        self.assertTrue(isinstance(message.sub_message, SuperMessage))

        # Add a basic attribute.
        self.assertTrue(builder.add_parameter(
            'pre.sub_message.sub_message.int64_value', ['10']))
        self.assertTrue(builder.add_parameter(
            'pre.sub_message.sub_message.string_value', ['hello']))

        self.assertTrue(10, message.sub_message.sub_message.int64_value)
        self.assertTrue('hello', message.sub_message.sub_message.string_value)


    def testAddParameter_NestedMessages(self):
        message = SuperSuperMessage()
        builder = to_url.URLEncodedRequestBuilder(message, prefix='pre.')

        # Add a repeated empty message.
        self.assertTrue(builder.add_parameter(
            'pre.sub_message.sub_messages-0', ['']))
        sub_message = message.sub_message.sub_messages[0]
        self.assertTrue(1, len(message.sub_message.sub_messages))
        self.assertTrue(isinstance(sub_message,
                                   test_util.OptionalMessage))
        self.assertEqual(None, getattr(sub_message, 'int64_value'))
        self.assertEqual(None, getattr(sub_message, 'string_value'))
        self.assertEqual(None, getattr(sub_message, 'enum_value'))

        # Add a repeated message with value.
        self.assertTrue(builder.add_parameter(
            'pre.sub_message.sub_messages-1.int64_value', ['10']))
        self.assertTrue(2, len(message.sub_message.sub_messages))
        self.assertTrue(10, message.sub_message.sub_messages[1].int64_value)

        # Add another value to the same nested message.
        self.assertTrue(builder.add_parameter(
            'pre.sub_message.sub_messages-1.string_value', ['a string']))
        self.assertTrue(2, len(message.sub_message.sub_messages))
        self.assertEqual(10, message.sub_message.sub_messages[1].int64_value)
        self.assertEqual('a string',
                          message.sub_message.sub_messages[1].string_value)

    def testAddParameter_RepeatedValues(self):
        message = test_util.RepeatedMessage()
        builder = to_url.URLEncodedRequestBuilder(message, prefix='pre.')

        self.assertTrue(builder.add_parameter('pre.int64_value-0', ['20']))
        self.assertTrue(builder.add_parameter('pre.int64_value-1', ['30']))
        self.assertEqual([20, 30], message.int64_value)

        self.assertTrue(builder.add_parameter('pre.string_value-0', ['hi']))
        self.assertTrue(builder.add_parameter('pre.string_value-1', ['lo']))
        self.assertTrue(builder.add_parameter('pre.string_value-1', ['dups overwrite']))
        self.assertEqual(['hi', 'dups overwrite'], message.string_value)

    def testAddParameter_InvalidValuesMayRepeat(self):
        message = test_util.OptionalMessage()
        builder = to_url.URLEncodedRequestBuilder(message, prefix='pre.')

        self.assertFalse(builder.add_parameter('nothing', [1, 2, 3]))

    def testAddParameter_RepeatedParameters(self):
        message = test_util.OptionalMessage()
        builder = to_url.URLEncodedRequestBuilder(message, prefix='pre.')

        self.assertRaises(messages.DecodeError,
                          builder.add_parameter,
                          'pre.int64_value',
                          [1, 2, 3])
        self.assertRaises(messages.DecodeError,
                          builder.add_parameter,
                          'pre.int64_value',
            [])

    def testAddParameter_UnexpectedNestedValue(self):
        """Test getting a nested value on a non-message sub-field."""
        message = test_util.HasNestedMessage()
        builder = to_url.URLEncodedRequestBuilder(message, prefix='pre.')

        self.assertFalse(builder.add_parameter('pre.nested.a_value.whatever',
                                               ['1']))

    def testInvalidFieldFormat(self):
        message = test_util.OptionalMessage()
        builder = to_url.URLEncodedRequestBuilder(message, prefix='pre.')

        self.assertFalse(builder.add_parameter('pre.illegal%20', ['1']))

    def testAddParameter_UnexpectedNestedValue2(self):
        """Test getting a nested value on a non-message sub-field

        There is an odd corner case where if trying to insert a repeated value
        on an nested repeated message that would normally succeed in being created
        should fail.  This case can only be tested when the first message of the
        nested messages already exists.

        Another case is trying to access an indexed value nested within a
        non-message field.
        """

        class HasRepeated(messages.Message):
            values = messages.IntegerField(repeated=True)

        class HasNestedRepeated(messages.Message):
            nested = messages.MessageField(HasRepeated, repeated=True)


        message = HasNestedRepeated()
        builder = to_url.URLEncodedRequestBuilder(message, prefix='pre.')

        self.assertTrue(builder.add_parameter('pre.nested-0.values-0', ['1']))
        # Try to create an indexed value on a non-message field.
        self.assertFalse(builder.add_parameter('pre.nested-0.values-0.unknown-0',
                                               ['1']))
        # Try to create an out of range indexed field on an otherwise valid
        # repeated message field.
        self.assertFalse(builder.add_parameter('pre.nested-1.values-1', ['1']))


class ProtourlencodeConformanceTest(test_util.TestCase,
                                    test_util.PytractsConformanceTestBase):
    PROTOLIB = to_url

    encoded_partial = urlencode(sorted([('double_value', 1.23),
                                        ('int64_value', -100000000000),
                                        ('int32_value', 1020),
                                        ('string_value', u'a string'),
                                        ('enum_value', 'VAL2'),
    ], key=lambda kv: kv[0]))

    encoded_full = urlencode(sorted([('double_value', 1.23),
                                     ('float_value', -2.5),
                                     ('int64_value', -100000000000),
                                     ('uint64_value', 102020202020),
                                     ('int32_value', 1020),
                                     ('bool_value', 'true'),
                                     ('string_value', u'a string\u044f'.encode('utf-8')),
                                     ('bytes_value', 'YSBieXRlc//+'),
                                     ('enum_value', 'VAL2'),
    ], key=lambda kv: kv[0]))

    encoded_repeated = urlencode(sorted([('double_value', 1.23),
                                         ('double_value', 2.3),
                                         ('float_value', -2.5),
                                         ('float_value', 0.5),
                                         ('int64_value', -100000000000),
                                         ('int64_value', 20),
                                         ('uint64_value', 102020202020),
                                         ('uint64_value', 10),
                                         ('int32_value', 1020),
                                         ('int32_value', 718),
                                         ('bool_value', 'true'),
                                         ('bool_value', 'false'),
                                         ('string_value', u'a string\u044f'.encode('utf-8')),
                                         ('string_value', u'another string'.encode('utf-8')),
                                         ('bytes_value', 'YSBieXRlc//+'),
                                         ('bytes_value', 'YW5vdGhlciBieXRlcw=='),
                                         ('enum_value', 'VAL2'),
                                         ('enum_value', 'VAL1'),
    ], key=lambda kv: kv[0]))

    encoded_nested = urlencode(sorted([('nested.a_value', 'a string')], key=lambda kv: kv[0]))

    encoded_repeated_nested = urlencode(sorted([('repeated_nested-0.a_value', 'a string'),
                                                       ('repeated_nested-1.a_value', 'another string'),
    ], key=lambda kv: kv[0]))

    unexpected_tag_message = 'unexpected=whatever'

    encoded_default_assigned = urlencode(sorted([('a_value', 'a default'),], key=lambda kv: kv[0]))

    encoded_nested_empty = urlencode(sorted([('nested', '')], key=lambda kv: kv[0]))

    encoded_repeated_nested_empty = urlencode(sorted([('repeated_nested-0', ''),
                                                      ('repeated_nested-1', '')], key=lambda kv: kv[0]))

    encoded_extend_message = urlencode(sorted([('int64_value-0', 400),
                                               ('int64_value-1', 50),
                                               ('int64_value-2', 6000)], key=lambda kv: kv[0]))

    encoded_string_types = urlencode(
        sorted([('string_value', 'Latin')], key=lambda kv: kv[0]))

    encoded_invalid_enum = urlencode([('enum_value', 'undefined')])

    def testParameterPrefix(self):
        """Test using the 'prefix' parameter to encode_message."""

        class MyMessage(messages.Message):
            number = messages.IntegerField()
            names = messages.StringField(repeated=True)

        message = MyMessage()
        message.number = 10
        message.names = [u'Fred', u'Lisa']

        encoded_message = to_url.encode_message(message, prefix='prefix-')
        self.assertEqual({'prefix-number': ['10'],
                           'prefix-names': ['Fred', 'Lisa']},
                          parse_qs(encoded_message))

        self.assertEqual(message, to_url.decode_message(MyMessage,
                                                                 encoded_message,
                                                                 prefix='prefix-'))

    def testProtourlencodeUnrecognizedField(self):
        """Test that unrecognized fields are saved and can be accessed."""

        class MyMessage(messages.Message):
            number = messages.IntegerField()

        decoded = to_url.decode_message(MyMessage,
                                                self.unexpected_tag_message)
        self.assertEqual(1, len(decoded.all_unrecognized_fields()))
        self.assertEqual('unexpected', decoded.all_unrecognized_fields()[0])
        # Unknown values set to a list of however many values had that name.
        self.assertEqual((['whatever'], messages.Variant.STRING),
                          decoded.get_unrecognized_field_info('unexpected'))

        repeated_unknown = urlencode([('repeated', 400),
                                      ('repeated', 'test'),
                                      ('repeated', '123.456')])
        decoded2 = to_url.decode_message(MyMessage, repeated_unknown)
        self.assertEqual((['400', 'test', '123.456'], messages.Variant.STRING),
                          decoded2.get_unrecognized_field_info('repeated'))

    def testDecodeUUID(self):
        from uuid import UUID
        class Foo(messages.Message):
            bar = messages.UUIDField()

        m = to_url.decode_message(Foo, 'bar=06335e84-2872-4914-8c5d-3ed07d2a2f16')
        self.assertEqual(UUID("06335e84-2872-4914-8c5d-3ed07d2a2f16"), m.bar)

    def testDecodeUUIDInvalid(self):
        from uuid import UUID
        class Foo(messages.Message):
            bar = messages.UUIDField()

        with self.assertRaises(messages.DecodeError):
            to_url.decode_message(Foo, 'bar=bad')

    def testDecodeDateTimeIso8601(self):
        class MyMessage(messages.Message):
            a_datetime = messages.DateTimeISO8601Field()

        m = to_url.decode_message(MyMessage, 'a_datetime=2012-09-30T15:31:50.262000')
        self.assertEqual(datetime(2012, 9, 30, 15, 31, 50, 262000), m.a_datetime)

        m = to_url.decode_message(MyMessage, 'a_datetime=2012-09-30T15%3A31%3A50.262000')
        self.assertEqual(datetime(2012, 9, 30, 15, 31, 50, 262000), m.a_datetime)


    def testDecodeInvalidDateTimeIso8601(self):
        class MyMessage(messages.Message):
            a_datetime = messages.DateTimeISO8601Field()

        self.assertRaises(messages.DecodeError, to_url.decode_message,
                          MyMessage, 'a_datetime=invalid')

    def testDecodeDateTimeMsInteger(self):
        class MyMessage(messages.Message):
            a_datetime = messages.DateTimeMsIntegerField()

        m = to_url.decode_message(MyMessage, 'a_datetime=1349019110262')
        self.assertEqual(datetime(2012, 9, 30, 15, 31, 50, 262000), m.a_datetime)

        m = to_url.decode_message(MyMessage, 'a_datetime=1349019110262')
        self.assertEqual(datetime(2012, 9, 30, 15, 31, 50, 262000), m.a_datetime)

    def testDecodeInvalidDateTimeMsInteger(self):
        class MyMessage(messages.Message):
            a_datetime = messages.DateTimeISO8601Field()

        self.assertRaises(messages.DecodeError, to_url.decode_message,
                          MyMessage, 'a_datetime=invalid')

    def test_decode_message_from_url(self):
        class AnimalSounds(messages.Message):
            cow = messages.StringField()
            dog = messages.StringField()

        foo = AnimalSounds(cow='moo', dog='woof')
        self.assertEqual(foo, to_url.decode_message_from_url(AnimalSounds, "http://example.com?cow=moo&dog=woof"))

    def test_decode_message_from_url_repeated(self):
        class Animals(messages.Message):
            animals = messages.StringField(repeated=True)
            number = messages.IntegerField()

        tmp = Animals(animals=['dog', 'cat'], number=2)
        self.assertEqual(tmp, to_url.decode_message_from_url(Animals, "http://example.com?animals=dog&animals=cat&number=2"))

    def test_decode_message_from_url_repeated_alias(self):
        class Animals(messages.Message):
            animals = messages.StringField(name='a', repeated=True)
            number = messages.IntegerField()

        tmp = Animals(animals=['dog', 'cat'], number=2)
        self.assertEqual(tmp, to_url.decode_message_from_url(Animals, "http://example.com?a=dog&a=cat&number=2"))

    def test_decode_message_from_url_repeated_alias_dashes(self):
        class Animals(messages.Message):
            animals = messages.StringField(name='a-m', repeated=True)
            number = messages.IntegerField()

        tmp = Animals(animals=['dog', 'cat'], number=2)
        self.assertEqual(tmp, to_url.decode_message_from_url(Animals, "http://example.com?a-m=dog&a-m=cat&number=2"))

    def test_encode_message_from_url_repeated_alias(self):
        class Animals(messages.Message):
            animals = messages.StringField(name='a', repeated=True)
            number = messages.IntegerField()

        tmp = Animals(animals=['dog', 'cat'], number=2)
        self.assertEqual("a=dog&a=cat&number=2", to_url.encode_message(tmp))

    def test_decode_message_from_url_repeated_not_filled_out(self):
        class Animals(messages.Message):
            animals = messages.StringField(repeated=True)
            number = messages.IntegerField()

        result = to_url.decode_message_from_url(Animals, "http://example.com?number=2")
        self.assertFalse(Animals.animals.is_set(result))
        self.assertEqual([], result.animals)

    def test_decode_message_from_url_repeated_message(self):
        class Animal(messages.Message):
            name = messages.StringField()
            size = messages.IntegerField()

        class Animals(messages.Message):
            animals = messages.MessageField(Animal, repeated=True)
            number = messages.IntegerField()

        dog = Animal(name='dog', size=12)
        cat = Animal(name='cat', size=10)
        tmp = Animals(animals=[dog, cat], number=2)

        self.assertEqual(tmp, to_url.decode_message_from_url(Animals, "http://example.com?animals-0.name=dog&animals-0.size=12&animals-1.name=cat&animals-1.size=10&number=2"))

    def test_encode_message_repeated_message_field(self):
        class Animal(messages.Message):
            name = messages.StringField()
            size = messages.IntegerField()

        class Animals(messages.Message):
            animals = messages.MessageField(Animal, repeated=True)
            number = messages.IntegerField()

        dog = Animal(name='dog', size=12)
        cat = Animal(name='cÄt', size=10)
        tmp = Animals(animals=[dog, cat], number=2)

        encoded_message = to_url.encode_message(tmp)
        self.assertEqual({'number': ['2'],
                           'animals-0.name': ['dog'],
                           'animals-0.size': ['12'],
                           'animals-1.name': ['cÄt'],
                           'animals-1.size': ['10']},
                           parse_qs(encoded_message))

        self.assertEqual(tmp, to_url.decode_message(Animals, encoded_message))

if __name__ == '__main__':
    unittest.main()
