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

"""Tests for pytracts.to_json."""
from tests import test_util

__author__ = 'rafek@google.com (Rafe Kaplan)'

import sys
import unittest
from datetime import datetime, date, time

from pytracts import message_types
from pytracts import messages
from pytracts import to_json

import json

try:
    from importlib import reload
except ImportError:
    try:
        from imp import reload
    except:
        # Python 2.x
        reload = reload

class CustomField(messages.MessageField):
    """Custom MessageField class."""

    type = int
    message_type = message_types.VoidMessage

    def __init__(self, **kwargs):
        super(CustomField, self).__init__(self.message_type, **kwargs)

    def value_to_message(self, value):
        return self.message_type()


class MyMessage(messages.Message):
    """Test message containing various types."""

    class Color(messages.Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    class Nested(messages.Message):
        nested_value = messages.StringField()

    a_string = messages.StringField()
    an_integer = messages.IntegerField()
    a_float = messages.FloatField()
    a_boolean = messages.BooleanField()
    an_enum = messages.EnumField(Color)
    a_nested = messages.MessageField(Nested)
    a_repeated = messages.IntegerField(repeated=True)
    a_repeated_float = messages.FloatField(repeated=True)
    a_datetime_iso8601 = messages.DateTimeISO8601Field()
    a_repeated_datetime_iso8601 = messages.DateTimeISO8601Field(repeated=True)
    a_datetime_ms_integer = messages.DateTimeMsIntegerField()
    a_repeated_datetime_ms_integer = messages.DateTimeMsIntegerField(repeated=True)
    a_custom = CustomField()
    a_repeated_custom = CustomField(repeated=True)


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):
    MODULE = to_json


# TODO(rafek): Convert this test to the compliance test in test_util.
class ProtojsonTest(test_util.TestCase,
                    test_util.PytractsConformanceTestBase):
    """Test JSON encoding and decoding."""

    PROTOLIB = to_json

    def CompareEncoded(self, expected_encoded, actual_encoded):
        """JSON encoding will be laundered to remove string differences."""
        self.assertEqual(json.loads(expected_encoded),
                          json.loads(actual_encoded))

    encoded_empty_message = '{}'

    encoded_partial = """{
    "double_value": 1.23,
    "int64_value": -100000000000,
    "int32_value": 1020,
    "string_value": "a string",
    "enum_value": "VAL2"
  }
  """

    encoded_full = """{
    "double_value": 1.23,
    "float_value": -2.5,
    "int64_value": -100000000000,
    "uint64_value": 102020202020,
    "int32_value": 1020,
    "bool_value": true,
    "string_value": "a string\u044f",
    "bytes_value": "YSBieXRlc//+",
    "enum_value": "VAL2"
  }
  """

    encoded_repeated = """{
    "double_value": [1.23, 2.3],
    "float_value": [-2.5, 0.5],
    "int64_value": [-100000000000, 20],
    "uint64_value": [102020202020, 10],
    "int32_value": [1020, 718],
    "bool_value": [true, false],
    "string_value": ["a string\u044f", "another string"],
    "bytes_value": ["YSBieXRlc//+", "YW5vdGhlciBieXRlcw=="],
    "enum_value": ["VAL2", "VAL1"]
  }
  """

    encoded_nested = """{
    "nested": {
      "a_value": "a string"
    }
  }
  """

    encoded_repeated_nested = """{
    "repeated_nested": [{"a_value": "a string"},
                        {"a_value": "another string"}]
  }
  """

    unexpected_tag_message = '{"unknown": "value"}'

    encoded_default_assigned = '{"a_value": "a default"}'

    encoded_nested_empty = '{"nested": {}}'

    encoded_repeated_nested_empty = '{"repeated_nested": [{}, {}]}'

    encoded_extend_message = '{"int64_value": [400, 50, 6000]}'

    encoded_string_types = '{"string_value": "Latin"}'

    encoded_invalid_enum = '{"enum_value": "undefined"}'

    def testConvertIntegerToFloat(self):
        """Test that integers passed in to float fields are converted.

        This is necessary because JSON outputs integers for numbers with 0 decimals.
        """
        message = to_json.decode_message(MyMessage, '{"a_float": 10}')

        self.assertTrue(isinstance(message.a_float, float))
        self.assertEqual(10.0, message.a_float)

    def testConvertStringToNumbers(self):
        """Test that strings passed to integer fields are converted."""
        message = to_json.decode_message(MyMessage,
                                           """{"an_integer": "10",
                                               "a_float": "3.5",
                                               "a_repeated": ["1", "2"],
                                               "a_repeated_float": ["1.5", "2", 10]
                                               }""")

        self.assertEqual(MyMessage(an_integer=10,
                                    a_float=3.5,
                                    a_repeated=[1, 2],
                                    a_repeated_float=[1.5, 2.0, 10.0]),
                          message)

    def testWrongTypeAssignment(self):
        """Test when wrong type is assigned to a field."""
        self.assertRaises(messages.ValidationError,
                          to_json.decode_message,
                          MyMessage, '{"a_string": 10}')
        self.assertRaises(messages.ValidationError,
                          to_json.decode_message,
                          MyMessage, '{"an_integer": 10.2}')
        self.assertRaises(messages.ValidationError,
                          to_json.decode_message,
                          MyMessage, '{"an_integer": "10.2"}')

    def testNumericEnumeration(self):
        """Test that numbers work for enum values."""
        message = to_json.decode_message(MyMessage, '{"an_enum": 2}')

        expected_message = MyMessage()
        expected_message.an_enum = MyMessage.Color.GREEN

        self.assertEqual(expected_message, message)

    def testNullValues(self):
        """Test that null values overwrite existing values."""
        m = MyMessage()
        m.an_integer = None
        m.a_nested = None

        self.assertEqual(m,
                          to_json.decode_message(MyMessage,
                                                   ('{"an_integer": null,'
                                                    ' "a_nested": null'
                                                    '}')))

    def testEmptyList(self):
        """Test that empty lists are not ignored."""
        m = MyMessage()
        m.a_repeated = []
        self.assertEqual(m,
                          to_json.decode_message(MyMessage,
                                                   '{"a_repeated": []}'))

    def testNotJSON(self):
        """Test error when string is not valid JSON."""
        self.assertRaises(ValueError,
                          to_json.decode_message, MyMessage, '{this is not json}')

    def testDoNotEncodeStrangeObjects(self):
        """Test trying to encode a strange object.

        The main purpose of this test is to complete coverage.  It ensures that
        the default behavior of the JSON encoder is preserved when someone tries to
        serialized an unexpected type.
        """

        class BogusObject(object):
            def check_initialized(self):
                pass

        self.assertRaises(TypeError,
                          to_json.encode_message,
                          BogusObject())

    def testMergeEmptyString(self):
        """Test merging the empty or space only string."""
        message = to_json.decode_message(test_util.OptionalMessage, '')
        self.assertEqual(test_util.OptionalMessage(), message)

        message = to_json.decode_message(test_util.OptionalMessage, ' ')
        self.assertEqual(test_util.OptionalMessage(), message)

    def testProtojsonUnrecognizedFieldName(self):
        """Test that unrecognized fields are saved and can be accessed."""
        decoded = to_json.decode_message(MyMessage,
                                           ('{"an_integer": 1, "unknown_val": 2}'))
        self.assertEqual(decoded.an_integer, 1)
        self.assertEqual(1, len(decoded.all_unrecognized_fields()))
        self.assertEqual('unknown_val', decoded.all_unrecognized_fields()[0])
        self.assertEqual((2, messages.Variant.INT64),
                          decoded.get_unrecognized_field_info('unknown_val'))

    def testProtojsonUnrecognizedFieldNumber(self):
        """Test that unrecognized fields are saved and can be accessed."""
        decoded = to_json.decode_message(
            MyMessage,
            '{"an_integer": 1, "1001": "unknown", "-123": "negative", '
            '"456_mixed": 2}')
        self.assertEqual(decoded.an_integer, 1)
        self.assertEqual(3, len(decoded.all_unrecognized_fields()))
        self.assertIn(1001, decoded.all_unrecognized_fields())
        self.assertEqual(('unknown', messages.Variant.STRING),
                          decoded.get_unrecognized_field_info(1001))
        self.assertIn('-123', decoded.all_unrecognized_fields())
        self.assertEqual(('negative', messages.Variant.STRING),
                          decoded.get_unrecognized_field_info('-123'))
        self.assertIn('456_mixed', decoded.all_unrecognized_fields())
        self.assertEqual((2, messages.Variant.INT64),
                          decoded.get_unrecognized_field_info('456_mixed'))

    def testProtojsonUnrecognizedNull(self):
        """Test that unrecognized fields that are None are skipped."""
        decoded = to_json.decode_message(
            MyMessage,
            '{"an_integer": 1, "unrecognized_null": null}')
        self.assertEqual(decoded.an_integer, 1)
        self.assertEqual(decoded.all_unrecognized_fields(), [])

    def testUnrecognizedFieldVariants(self):
        """Test that unrecognized fields are mapped to the right variants."""
        for encoded, expected_variant in (
                ('{"an_integer": 1, "unknown_val": 2}', messages.Variant.INT64),
                ('{"an_integer": 1, "unknown_val": 2.0}', messages.Variant.DOUBLE),
                ('{"an_integer": 1, "unknown_val": "string value"}',
                 messages.Variant.STRING),
                ('{"an_integer": 1, "unknown_val": [1, 2, 3]}', messages.Variant.INT64),
                ('{"an_integer": 1, "unknown_val": [1, 2.0, 3]}',
                 messages.Variant.DOUBLE),
                ('{"an_integer": 1, "unknown_val": [1, "foo", 3]}',
                 messages.Variant.STRING),
                ('{"an_integer": 1, "unknown_val": true}', messages.Variant.BOOL)):
            decoded = to_json.decode_message(MyMessage, encoded)
            self.assertEqual(decoded.an_integer, 1)
            self.assertEqual(1, len(decoded.all_unrecognized_fields()))
            self.assertEqual('unknown_val', decoded.all_unrecognized_fields()[0])
            _, decoded_variant = decoded.get_unrecognized_field_info('unknown_val')
            self.assertEqual(expected_variant, decoded_variant)

    def testDecodeDateTime(self):
        for datetime_string, datetime_vals in (
                ('2012-09-30T15:31:50.262', (2012, 9, 30, 15, 31, 50, 262000)),
                ('2012-09-30T15:31:50', (2012, 9, 30, 15, 31, 50, 0))):
            message = to_json.decode_message(
                MyMessage, '{"a_datetime_iso8601": "%s"}' % datetime_string)
            expected_message = MyMessage(
                a_datetime_iso8601=datetime(*datetime_vals))

            self.assertEqual(expected_message, message)

    def testDecodeInvalidDateTime(self):
        self.assertRaises(messages.DecodeError, to_json.decode_message,
                          MyMessage, '{"a_datetime_iso8601": "invalid"}')

    def testEncodeDateTimeISO8601(self):
        for datetime_string, datetime_vals in (
                ('2012-09-30T15:31:50.262000', (2012, 9, 30, 15, 31, 50, 262000)),
                ('2012-09-30T15:31:50.262123', (2012, 9, 30, 15, 31, 50, 262123)),
                ('2012-09-30T15:31:50', (2012, 9, 30, 15, 31, 50, 0))):
            decoded_message = to_json.encode_message(
                MyMessage(a_datetime_iso8601=datetime(*datetime_vals)))
            expected_decoding = '{"a_datetime_iso8601": "%s"}' % datetime_string
            self.CompareEncoded(expected_decoding, decoded_message)

    def testDecodeRepeatedDateTimeISO8601(self):
        message = to_json.decode_message(
            MyMessage,
            '{"a_repeated_datetime_iso8601": ["2012-09-30T15:31:50.262", '
            '"2010-01-21T09:52:00", "2000-01-01T01:00:59.999999"]}')
        expected_message = MyMessage(
            a_repeated_datetime_iso8601=[
                datetime(2012, 9, 30, 15, 31, 50, 262000),
                datetime(2010, 1, 21, 9, 52),
                datetime(2000, 1, 1, 1, 0, 59, 999999)])

        self.assertEqual(expected_message, message)

    def testDecodeDateTimeMsInteger(self):
        for datetime_int, datetime_vals in (
                (1349019110262, (2012, 9, 30, 15, 31, 50, 262000)),
                (1349019110000, (2012, 9, 30, 15, 31, 50, 0))):
            message = to_json.decode_message(
                MyMessage, '{"a_datetime_ms_integer": %d}' % datetime_int)
            expected_message = MyMessage(
                a_datetime_ms_integer=datetime(*datetime_vals))

            self.assertEqual(expected_message, message)

    def testDecodeInvalidDateTimeMsInteger(self):
        self.assertRaises(messages.DecodeError, to_json.decode_message,
                          MyMessage, '{"a_datetime_ms_integer": "invalid"}')

    def testEncodeDateTimeMsInteger(self):
        for datetime_int, datetime_vals in (
                (1349019110262, (2012, 9, 30, 15, 31, 50, 262000)),
                (1349019110262, (2012, 9, 30, 15, 31, 50, 262123)),
                (1349019110000, (2012, 9, 30, 15, 31, 50, 0))):
            decoded_message = to_json.encode_message(
                MyMessage(a_datetime_ms_integer=datetime(*datetime_vals)))
            expected_decoding = '{"a_datetime_ms_integer": %d}' % datetime_int
            self.CompareEncoded(expected_decoding, decoded_message)

    def testDecodeRepeatedDateTimeMsInteger(self):
        message = to_json.decode_message(
            MyMessage,
            '{"a_repeated_datetime_ms_integer": [1349019110262, '
            '1264067520000, 946688459999]}')
        expected_message = MyMessage(
            a_repeated_datetime_ms_integer=[
                datetime(2012, 9, 30, 15, 31, 50, 262000),
                datetime(2010, 1, 21, 9, 52),
                datetime(2000, 1, 1, 1, 0, 59, 999000)])

        self.assertEqual(expected_message, message)

    def testDecodeCustom(self):
        message = to_json.decode_message(MyMessage, '{"a_custom": 1}')
        self.assertEqual(MyMessage(a_custom=1), message)

    def testDecodeInvalidCustom(self):
        self.assertRaises(messages.ValidationError, to_json.decode_message,
                          MyMessage, '{"a_custom": "invalid"}')

    def testEncodeCustom(self):
        decoded_message = to_json.encode_message(MyMessage(a_custom=1))
        self.CompareEncoded('{"a_custom": 1}', decoded_message)

    def testDecodeRepeatedCustom(self):
        message = to_json.decode_message(
            MyMessage, '{"a_repeated_custom": [1, 2, 3]}')
        self.assertEqual(MyMessage(a_repeated_custom=[1, 2, 3]), message)

    def testDecodeBadBase64BytesField(self):
        """Test decoding improperly encoded base64 bytes value."""
        self.assertRaisesWithRegexpMatch(
            messages.DecodeError,
            '.*Invalid base64-encoded string.*',
            to_json.decode_message,
            test_util.OptionalMessage,
            '{"bytes_value": "abcdefghijklmnopq"}')

    def test_has_value_assigned(self):
        class Foo(messages.Message):
            not_set = messages.StringField()
            set_null = messages.StringField()

        message = to_json.decode_message(Foo, '{"set_null": null}')
        self.assertFalse(message.has_value_assigned('not_set'))
        self.assertTrue(message.has_value_assigned('set_null'))
        self.assertIsNone(message.not_set)
        self.assertIsNone(message.set_null)

    def test_has_value_assigned_repeated(self):
        class Foo(messages.Message):
            pete = messages.StringField(repeated=True)

        message = to_json.decode_message(Foo, '{"pete": []}')
        self.assertTrue(message.has_value_assigned('pete'))

        message = to_json.decode_message(Foo, '{"pete": ["sat"]}')
        self.assertTrue(message.has_value_assigned('pete'))

        message = to_json.decode_message(Foo, '{"pete": ["sat", "in", "a", "boat"]}')
        self.assertTrue(message.has_value_assigned('pete'))

    def test_repeated_value_null_not_allowed(self):
        class Foo(messages.Message):
            pete = messages.StringField(repeated=True)

        self.assertRaises(messages.ValidationError, lambda: to_json.decode_message(Foo, '{"pete": null}'))

    def test_explicit_field_name(self):
        class Foo(messages.Message):
            bob = messages.StringField(name="robert")
            ryan = messages.StringField()

        m = to_json.decode_message(Foo, '{"robert": "smith", "ryan": "morlok"}')

        self.assertEqual("smith", m.bob)
        self.assertEqual("morlok", m.ryan)

        f = Foo()
        f.bob = "smith"
        f.ryan = "morlok"

        self.assertEqual(json.loads('{"robert": "smith", "ryan": "morlok"}'), json.loads(to_json.encode_message(f)))

    def test_assigned_values_rendered(self):
        class Animals(messages.Message):
            bird = messages.StringField(repeated=True)
            cow = messages.StringField()

        a = Animals()
        self.assertEqual('{}', to_json.encode_message(a))

        a = Animals()
        a.cow = "moo"
        self.assertEqual('{"cow": "moo"}', to_json.encode_message(a))

        a = Animals()
        a.cow = None
        self.assertEqual('{"cow": null}', to_json.encode_message(a))

        a = Animals()
        a.bird = []
        self.assertEqual('{"bird": []}', to_json.encode_message(a))

        a = Animals()
        a.bird = ["quack", "cheep", "honk"]
        self.assertEqual('{"bird": ["quack", "cheep", "honk"]}', to_json.encode_message(a))

        a = Animals()
        a.cow = "moo"
        a.bird = ["quack", "cheep", "honk"]
        self.assertEqual(json.loads('{"bird": ["quack", "cheep", "honk"], "cow": "moo"}'), json.loads(to_json.encode_message(a)))

    def test_untyped_field_encode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField()

        f = Foo()
        self.assertEqual('{}', to_json.encode_message(f))

        f = Foo()
        f.bar = 123
        self.assertEqual('{"bar": 123}', to_json.encode_message(f))

        f = Foo()
        f.bar = "meow"
        self.assertEqual('{"bar": "meow"}', to_json.encode_message(f))

        f = Foo()
        f.bar = True
        self.assertEqual('{"bar": true}', to_json.encode_message(f))

        f = Foo()
        f.bar = 1.23
        self.assertEqual('{"bar": 1.23}', to_json.encode_message(f))

        f = Foo()
        f.bar = None
        self.assertEqual('{"bar": null}', to_json.encode_message(f))

        f = Foo()
        f.bar = [[123, 1.23, "woof", True], "meow"]
        self.assertEqual('{"bar": [[123, 1.23, "woof", true], "meow"]}', to_json.encode_message(f))

    def test_untyped_field_decode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField()

        f = Foo()
        self.assertEqual(f, to_json.decode_message(Foo, '{}'))

        f = Foo()
        f.bar = 123
        self.assertEqual(f, to_json.decode_message(Foo, '{"bar": 123}'))

        f = Foo()
        f.bar = "meow"
        self.assertEqual(f, to_json.decode_message(Foo, '{"bar": "meow"}'))

        f = Foo()
        f.bar = True
        self.assertEqual(f, to_json.decode_message(Foo, '{"bar": true}'))

        f = Foo()
        f.bar = 1.23
        self.assertEqual(f, to_json.decode_message(Foo, '{"bar": 1.23}'))

        f = Foo()
        f.bar = 1.23
        self.assertEqual(f, to_json.decode_message(Foo, '{"bar": 1.23}'))

        f = Foo()
        f.bar = None
        self.assertEqual(f, to_json.decode_message(Foo, '{"bar": null}'))

        f = Foo()
        f.bar = [[123, 1.23, "woof", True], "meow"]
        self.assertEqual(f, to_json.decode_message(Foo, '{"bar": [[123, 1.23, "woof", true], "meow"]}'))


    def test_untyped_field_repeated_encode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField(repeated=True)

        f = Foo()
        f.bar = [123, "woof", 1.23, True]
        self.assertEqual('{"bar": [123, "woof", 1.23, true]}', to_json.encode_message(f))

    def test_untyped_field_repeated_decode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField(repeated=True)

        f = Foo()
        f.bar = [123, "woof", 1.23, True]
        self.assertEqual(f, to_json.decode_message(Foo, '{"bar": [123, "woof", 1.23, true]}'))

    def test_uuid_field_encode(self):
        from uuid import UUID

        class Foo(messages.Message):
            bar = messages.UUIDField()

        f = Foo(bar=UUID("06335e84-2872-4914-8c5d-3ed07d2a2f16"))
        self.assertEqual('{"bar": "06335e84-2872-4914-8c5d-3ed07d2a2f16"}', to_json.encode_message(f))

    def test_uuid_field_encode_repeated(self):
        from uuid import UUID
        class Foo(messages.Message):
            bar = messages.UUIDField(repeated=True)

        f = Foo(bar=[UUID("11115e84-2872-4914-8c5d-3ed07d2a2f16"), UUID("22225e84-2872-4914-8c5d-3ed07d2a2f16")])
        self.assertEqual(to_json.encode_message(f), '{"bar": ["11115e84-2872-4914-8c5d-3ed07d2a2f16", "22225e84-2872-4914-8c5d-3ed07d2a2f16"]}')

    def test_uuid_field_decode(self):
        from uuid import UUID
        class Foo(messages.Message):
            bar = messages.UUIDField()

        f = Foo(bar=UUID("06335e84-2872-4914-8c5d-3ed07d2a2f16"))
        self.assertEqual(f, to_json.decode_message(Foo, '{"bar": "06335e84-2872-4914-8c5d-3ed07d2a2f16"}'))

    def test_uuid_field_decode_repeated(self):
        from uuid import UUID
        class Foo(messages.Message):
            bar = messages.UUIDField(repeated=True)

        f = Foo(bar=[UUID("11115e84-2872-4914-8c5d-3ed07d2a2f16"), UUID("22225e84-2872-4914-8c5d-3ed07d2a2f16")])
        self.assertEqual(f, to_json.decode_message(Foo, '{"bar": ["11115e84-2872-4914-8c5d-3ed07d2a2f16", "22225e84-2872-4914-8c5d-3ed07d2a2f16"]}'))

    def test_uuid_field_decode_bad(self):
        class Foo(messages.Message):
            bar = messages.UUIDField()

        with self.assertRaises(messages.DecodeError):
            to_json.decode_message(Foo, '{"bar": "bad"}')

    def test_uuid_field_decode_bad_repeated(self):
        class Foo(messages.Message):
            bar = messages.UUIDField(repeated=True)

        with self.assertRaises(messages.DecodeError):
            to_json.decode_message(Foo, '{"bar": ["06335e84-2872-4914-8c5d-3ed07d2a2f16", "bad"]}')

    def test_dict_field_encode(self):
        class GrabBag(messages.Message):
            item_count = messages.IntegerField()
            items = messages.DictField()

        gb = GrabBag()
        self.assertEqual('{}', to_json.encode_message(gb))

        gb = GrabBag()
        gb.item_count = 123
        self.assertEqual('{"item_count": 123}', to_json.encode_message(gb))

        gb = GrabBag()
        gb.item_count = 123
        gb.items = {}
        self.assertEqual(json.loads('{"items": {}, "item_count": 123}'), json.loads(to_json.encode_message(gb)))

        gb = GrabBag()
        gb.item_count = 123
        gb.items = {'a': 'b', 'foo': 'bar'}
        self.assertEqual(json.loads('{"items": {"a": "b", "foo": "bar"}, "item_count": 123}'), json.loads(to_json.encode_message(gb)))

        gb = GrabBag()
        gb.items = {'a': datetime(2010, 11, 13, 14, 15, 16), 'b': date(2009, 10, 11), 'c': time(1, 2, 3)}
        self.assertEqual(json.loads('{"items": {"a": "2010-11-13T14:15:16", "c": "01:02:03", "b": "2009-10-11"}}'), json.loads(to_json.encode_message(gb)))

        gb = GrabBag()
        gb.items = {'nested': {'a': datetime(2010, 11, 13, 14, 15, 16), 'b': date(2009, 10, 11), 'c': time(1, 2, 3)}}
        self.assertEqual(json.loads('{"items": {"nested": {"a": "2010-11-13T14:15:16", "c": "01:02:03", "b": "2009-10-11"}}}'), json.loads(to_json.encode_message(gb)))

    def test_dict_field_decode(self):
        class GrabBag(messages.Message):
            item_count = messages.IntegerField()
            items = messages.DictField()

        gb = GrabBag()
        self.assertEqual(gb, to_json.decode_message(GrabBag, '{}'))

        gb = GrabBag()
        gb.item_count = 123
        self.assertEqual(gb, to_json.decode_message(GrabBag, '{"item_count": 123}'))

        gb = GrabBag()
        gb.item_count = 123
        gb.items = {}
        self.assertEqual(gb, to_json.decode_message(GrabBag, '{"items": {}, "item_count": 123}'))

        gb = GrabBag()
        gb.item_count = 123
        gb.items = {'a': 'b', 'foo': 'bar'}
        self.assertEqual(gb, to_json.decode_message(GrabBag, '{"items": {"a": "b", "foo": "bar"}, "item_count": 123}'))

        gb = GrabBag()
        gb.items = {u'a': u"2010-11-13T14:15:16", u'b': u"01:02:03", u'c': u"2009-10-11"}

        # Decode doesn't reverse dates in arbitrary dicts
        self.assertEqual(gb, to_json.decode_message(GrabBag, '{"items": {"a": "2010-11-13T14:15:16", "b": "01:02:03", "c": "2009-10-11"}}'))



class CustomJsonEncoder(to_json.JsonEncoder):
    def encode_field(self, field, value):
        return '{encoded}' + value

    def decode_field(self, field, value):
        return '{decoded}' + value


class CustomProtoJsonTest(test_util.TestCase):
    """Tests for serialization overriding functionality."""

    def setUp(self):
        self.to_json = CustomJsonEncoder()

    def testEncode(self):
        self.assertEqual('{"a_string": "{encoded}xyz"}', self.to_json.encode_message(MyMessage(a_string='xyz')))

    def testDecode(self):
        self.assertEqual(
            MyMessage(a_string='{decoded}xyz'),
            self.to_json.decode_message(MyMessage, '{"a_string": "xyz"}'))

    def testDefault(self):
        self.assertTrue(to_json.JsonEncoder.get_default(),
                        to_json.JsonEncoder.get_default())

        instance = CustomJsonEncoder()
        to_json.JsonEncoder.set_default(instance)
        self.assertTrue(instance is to_json.JsonEncoder.get_default())


class InvalidJsonModule(object):
    pass


class ValidJsonModule(object):
    class JSONEncoder(object):
        pass


class TestJsonDependencyLoading(test_util.TestCase):
    """Test loading various implementations of json."""

    def get_import(self):
        """Get __import__ method.

        Returns:
          The current __import__ method.
        """
        if isinstance(__builtins__, dict):
            return __builtins__['__import__']
        else:
            return __builtins__.__import__

    def set_import(self, new_import):
        """Set __import__ method.

        Args:
          new_import: Function to replace __import__.
        """
        if isinstance(__builtins__, dict):
            __builtins__['__import__'] = new_import
        else:
            __builtins__.__import__ = new_import

    def setUp(self):
        """Save original import function."""
        self.simplejson = sys.modules.pop('simplejson', None)
        self.json = sys.modules.pop('json', None)
        self.original_import = self.get_import()

        def block_all_jsons(name, *args, **kwargs):
            if 'json' in name:
                if name in sys.modules:
                    module = sys.modules[name]
                    module.name = name
                    return module
                raise ImportError('Unable to find %s' % name)
            else:
                return self.original_import(name, *args, **kwargs)

        self.set_import(block_all_jsons)

    def tearDown(self):
        """Restore original import functions and any loaded modules."""

        def reset_module(name, module):
            if module:
                sys.modules[name] = module
            else:
                sys.modules.pop(name, None)

        reset_module('simplejson', self.simplejson)
        reset_module('json', self.json)
        reload(to_json)

    def testLoadProtojsonWithValidJsonModule(self):
        """Test loading to_json module with a valid json dependency."""
        sys.modules['json'] = ValidJsonModule

        # This will cause to_json to reload with the default json module
        # instead of simplejson.
        reload(to_json)
        self.assertEqual('json', to_json.json.name)

    def testLoadProtojsonWithSimplejsonModule(self):
        """Test loading to_json module with simplejson dependency."""
        sys.modules['simplejson'] = ValidJsonModule

        # This will cause to_json to reload with the default json module
        # instead of simplejson.
        reload(to_json)
        self.assertEqual('simplejson', to_json.json.name)

    def testLoadProtojsonWithInvalidJsonModule(self):
        """Loading to_json module with an invalid json defaults to simplejson."""
        sys.modules['json'] = InvalidJsonModule
        sys.modules['simplejson'] = ValidJsonModule

        # Ignore bad module and default back to simplejson.
        reload(to_json)
        self.assertEqual('simplejson', to_json.json.name)

    def testLoadProtojsonWithInvalidJsonModuleAndNoSimplejson(self):
        """Loading to_json module with invalid json and no simplejson."""
        sys.modules['json'] = InvalidJsonModule

        # Bad module without simplejson back raises errors.
        self.assertRaisesWithRegexpMatch(
            ImportError,
            'json library "json" is not compatible with ProtoPy',
            reload,
            to_json)

    def testLoadProtojsonWithNoJsonModules(self):
        """Loading to_json module with invalid json and no simplejson."""
        # No json modules raise the first exception.
        self.assertRaisesWithRegexpMatch(
            ImportError,
            'Unable to find json',
            reload,
            to_json)


if __name__ == '__main__':
    unittest.main()
