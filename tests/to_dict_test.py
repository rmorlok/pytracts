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

"""Tests for pytracts.to_dict."""
from tests import test_util

__author__ = 'ryan@docalytics.com (Rafe Kaplan)'

import datetime
import sys
import unittest

from pytracts import message_types
from pytracts import messages
from pytracts import to_dict


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
    a_uuid = messages.UUIDField()
    a_repeated_uuid = messages.UUIDField(repeated=True)


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):
    MODULE = to_dict


# TODO(rafek): Convert this test to the compliance test in test_util.
class ProtoDictTest(test_util.TestCase,
                    test_util.PytractsConformanceTestBase):
    """Test dictionary encoding and decoding."""

    PROTOLIB = to_dict

    encoded_empty_message = {}

    encoded_partial = {
        "double_value": 1.23,
        "int64_value": -100000000000,
        "int32_value": 1020,
        "string_value": "a string",
        "enum_value": "VAL2"
    }

    encoded_full = {
        "double_value": 1.23,
        "float_value": -2.5,
        "int64_value": -100000000000,
        "uint64_value": 102020202020,
        "int32_value": 1020,
        "bool_value": True,
        "string_value": u"a string\u044f",
        "bytes_value": b"a bytes\xff\xfe",
        "enum_value": "VAL2"
    }

    encoded_repeated = {
        "double_value": [1.23, 2.3],
        "float_value": [-2.5, 0.5],
        "int64_value": [-100000000000, 20],
        "uint64_value": [102020202020, 10],
        "int32_value": [1020, 718],
        "bool_value": [True, False],
        "string_value": [u"a string\u044f", "another string"],
        "bytes_value": [b'a bytes\xff\xfe', b'another bytes'],
        "enum_value": ["VAL2", "VAL1"]
    }

    encoded_nested = {
        "nested": {
            "a_value": "a string"
        }
    }

    encoded_repeated_nested = {
        "repeated_nested": [{"a_value": "a string"},
                            {"a_value": "another string"}]
    }

    unexpected_tag_message = {"unknown": "value"}

    encoded_default_assigned = {"a_value": "a default"}

    encoded_nested_empty = {"nested": {}}

    encoded_repeated_nested_empty = {"repeated_nested": [{}, {}]}

    encoded_extend_message = {"int64_value": [400, 50, 6000]}

    encoded_string_types = {"string_value": "Latin"}

    encoded_invalid_enum = {"enum_value": "undefined"}

    def testConvertStringToNumbers(self):
        """Test that strings passed to integer fields are converted."""
        message = to_dict.decode_message(MyMessage,
                                           {"an_integer": "10",
                                            "a_float": "3.5",
                                            "a_repeated": ["1", "2"],
                                            "a_repeated_float": ["1.5", "2", 10]
                                           })

        self.assertEqual(MyMessage(an_integer=10,
                                    a_float=3.5,
                                    a_repeated=[1, 2],
                                    a_repeated_float=[1.5, 2.0, 10.0]),
                          message)

    def testWrongTypeAssignment(self):
        """Test when wrong type is assigned to a field."""
        self.assertRaises(messages.ValidationError,
                          to_dict.decode_message,
                          MyMessage, {"a_string": 10})
        self.assertRaises(messages.ValidationError,
                          to_dict.decode_message,
                          MyMessage, {"an_integer": 10.2})
        self.assertRaises(messages.ValidationError,
                          to_dict.decode_message,
                          MyMessage, {"an_integer": "10.2"})

    def testNumericEnumeration(self):
        """Test that numbers work for enum values."""
        message = to_dict.decode_message(MyMessage, {"an_enum": 2})

        expected_message = MyMessage()
        expected_message.an_enum = MyMessage.Color.GREEN

        self.assertEqual(expected_message, message)

    def testNullValues(self):
        """Test that null values overwrite existing values."""
        m = MyMessage()
        m.an_integer = None
        m.a_nested = None

        self.assertEqual(m, to_dict.decode_message(MyMessage, ({"an_integer": None, "a_nested": None})))

    def testEmptyList(self):
        """Test that empty lists are not ignored."""
        m = MyMessage()
        m.a_repeated = []
        self.assertEqual(m,
                          to_dict.decode_message(MyMessage,
                                                   {"a_repeated": []}))

    def testNotDict(self):
        """Test error when string is not valid dictionary."""
        self.assertRaises(ValueError, to_dict.decode_message, MyMessage, "this is not a dict")

    def testDoNotEncodeStrangeObjects(self):
        """Test trying to encode a strange object.

        The main purpose of this test is to complete coverage.  It ensures that
        the default behavior of the dictionary encoder is preserved when someone tries to
        serialized an unexpected type.
        """

        class BogusObject(object):
            def check_initialized(self):
                pass

        self.assertRaises(TypeError,
                          to_dict.encode_message,
                          BogusObject())

    def testProtodictUnrecognizedFieldName(self):
        """Test that unrecognized fields are saved and can be accessed."""
        decoded = to_dict.decode_message(MyMessage,
                                           ({"an_integer": 1, "unknown_val": 2}))
        self.assertEqual(decoded.an_integer, 1)
        self.assertEqual(1, len(decoded.all_unrecognized_fields()))
        self.assertEqual('unknown_val', decoded.all_unrecognized_fields()[0])
        self.assertEqual((2, messages.Variant.INT64),
                          decoded.get_unrecognized_field_info('unknown_val'))

    def testProtodictUnrecognizedFieldNumber(self):
        """Test that unrecognized fields are saved and can be accessed."""
        decoded = to_dict.decode_message(MyMessage, {"an_integer": 1, "1001": "unknown", "-123": "negative", "456_mixed": 2})
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

    def testProtodictUnrecognizedNull(self):
        """Test that unrecognized fields that are None are skipped."""
        decoded = to_dict.decode_message(
            MyMessage,
            {"an_integer": 1, "unrecognized_null": None})
        self.assertEqual(decoded.an_integer, 1)
        self.assertEqual(decoded.all_unrecognized_fields(), [])

    def testUnrecognizedFieldVariants(self):
        """Test that unrecognized fields are mapped to the right variants."""
        for encoded, expected_variant in (
                ({"an_integer": 1, "unknown_val": 2}, messages.Variant.INT64),
                ({"an_integer": 1, "unknown_val": 2.0}, messages.Variant.DOUBLE),
                ({"an_integer": 1, "unknown_val": "string value"},
                 messages.Variant.STRING),
                ({"an_integer": 1, "unknown_val": [1, 2, 3]}, messages.Variant.INT64),
                ({"an_integer": 1, "unknown_val": [1, 2.0, 3]},
                 messages.Variant.DOUBLE),
                ({"an_integer": 1, "unknown_val": [1, "foo", 3]},
                 messages.Variant.STRING),
                ({"an_integer": 1, "unknown_val": True}, messages.Variant.BOOL)):
            decoded = to_dict.decode_message(MyMessage, encoded)
            self.assertEqual(decoded.an_integer, 1)
            self.assertEqual(1, len(decoded.all_unrecognized_fields()))
            self.assertEqual('unknown_val', decoded.all_unrecognized_fields()[0])
            _, decoded_variant = decoded.get_unrecognized_field_info('unknown_val')
            self.assertEqual(expected_variant, decoded_variant)

    def testDecodeRepeatedUUID(self):
        from uuid import UUID
        message = to_dict.decode_message(MyMessage, {"a_repeated_uuid": [
            UUID("06335e84-2872-4914-8c5d-3ed07d2a2f16"),
            UUID("16335e84-2872-4914-8c5d-3ed07d2a2f16"),
            UUID("26335e84-2872-4914-8c5d-3ed07d2a2f16"),
        ]})

        expected_message = MyMessage(
            a_repeated_uuid=[
                UUID("06335e84-2872-4914-8c5d-3ed07d2a2f16"),
                UUID("16335e84-2872-4914-8c5d-3ed07d2a2f16"),
                UUID("26335e84-2872-4914-8c5d-3ed07d2a2f16"),])

        self.assertEqual(expected_message, message)

    def testDecodeRepeatedDateTimeIso8601(self):
        message = to_dict.decode_message(MyMessage, {"a_repeated_datetime_iso8601": [
            datetime.datetime(2012, 9, 30, 15, 31, 50, 262000),
            datetime.datetime(2010, 1, 21, 9, 52),
            datetime.datetime(2000, 1, 1, 1, 0, 59, 999999)
        ]})

        expected_message = MyMessage(
            a_repeated_datetime_iso8601=[
                datetime.datetime(2012, 9, 30, 15, 31, 50, 262000),
                datetime.datetime(2010, 1, 21, 9, 52),
                datetime.datetime(2000, 1, 1, 1, 0, 59, 999999)])

        self.assertEqual(expected_message, message)

    def testDecodeRepeatedDateTimeMsInteger(self):
        message = to_dict.decode_message(MyMessage, {"a_repeated_datetime_ms_integer": [
            datetime.datetime(2012, 9, 30, 15, 31, 50, 262000),
            datetime.datetime(2010, 1, 21, 9, 52),
            datetime.datetime(2000, 1, 1, 1, 0, 59, 999999)
        ]})

        expected_message = MyMessage(
            a_repeated_datetime_ms_integer=[
                datetime.datetime(2012, 9, 30, 15, 31, 50, 262000),
                datetime.datetime(2010, 1, 21, 9, 52),
                datetime.datetime(2000, 1, 1, 1, 0, 59, 999999)])

        self.assertEqual(expected_message, message)

    def testDecodeCustom(self):
        message = to_dict.decode_message(MyMessage, {"a_custom": 1})
        self.assertEqual(MyMessage(a_custom=1), message)

    def testDecodeInvalidCustom(self):
        self.assertRaises(messages.ValidationError, to_dict.decode_message,
                          MyMessage, {"a_custom": "invalid"})

    def testEncodeCustom(self):
        decoded_message = to_dict.encode_message(MyMessage(a_custom=1))
        self.assertEqual({"a_custom": 1}, decoded_message)

    def testDecodeRepeatedCustom(self):
        message = to_dict.decode_message(
            MyMessage, {"a_repeated_custom": [1, 2, 3]})
        self.assertEqual(MyMessage(a_repeated_custom=[1, 2, 3]), message)

    def test_has_value_assigned(self):
        class Foo(messages.Message):
            not_set = messages.StringField()
            set_null = messages.StringField()

        message = to_dict.decode_message(Foo, {"set_null": None})
        self.assertFalse(message.has_value_assigned('not_set'))
        self.assertTrue(message.has_value_assigned('set_null'))
        self.assertIsNone(message.not_set)
        self.assertIsNone(message.set_null)

    def test_has_value_assigned_repeated(self):
        class Foo(messages.Message):
            pete = messages.StringField(repeated=True)

        message = to_dict.decode_message(Foo, {"pete": []})
        self.assertTrue(message.has_value_assigned('pete'))

        message = to_dict.decode_message(Foo, {"pete": ["sat"]})
        self.assertTrue(message.has_value_assigned('pete'))

        message = to_dict.decode_message(Foo, {"pete": ["sat", "in", "a", "boat"]})
        self.assertTrue(message.has_value_assigned('pete'))

    def test_repeated_value_null_not_allowed(self):
        class Foo(messages.Message):
            pete = messages.StringField(repeated=True)

        self.assertRaises(messages.ValidationError, lambda: to_dict.decode_message(Foo, {"pete": None}))

    def test_explicit_field_name(self):
        class Foo(messages.Message):
            bob = messages.StringField(name="robert")
            ryan = messages.StringField()

        m = to_dict.decode_message(Foo, {"robert": "smith", "ryan": "morlok"})

        self.assertEqual("smith", m.bob)
        self.assertEqual("morlok", m.ryan)

        f = Foo()
        f.bob = "smith"
        f.ryan = "morlok"

        self.assertEqual({"robert": "smith", "ryan": "morlok"}, to_dict.encode_message(f))

    def test_explicit_field_name_repeated(self):
        class Foo(messages.Message):
            bob = messages.StringField(name="robert", repeated=True)
            ryan = messages.StringField()

        m = to_dict.decode_message(Foo, {"robert": ["smith", "jones"], "ryan": "morlok"})

        self.assertEqual(["smith", "jones"], m.bob)
        self.assertEqual("morlok", m.ryan)

        f = Foo()
        f.bob = ["smith", "jones"]
        f.ryan = "morlok"

        self.assertEqual({"robert": ["smith", "jones"], "ryan": "morlok"}, to_dict.encode_message(f))

    def test_explicit_field_name_round_trip(self):
        class Foo(messages.Message):
            bob = messages.StringField(name="robert")
            ryan = messages.StringField()

        f = Foo(bob="smith", ryan="morlok")
        m = to_dict.decode_message(Foo, to_dict.encode_message(f))

        self.assertEqual("smith", m.bob)
        self.assertEqual("morlok", m.ryan)

    def test_assigned_values_rendered(self):
        class Animals(messages.Message):
            bird = messages.StringField(repeated=True)
            cow = messages.StringField()

        a = Animals()
        self.assertEqual({}, to_dict.encode_message(a))

        a = Animals()
        a.cow = "moo"
        self.assertEqual({"cow": "moo"}, to_dict.encode_message(a))

        a = Animals()
        a.cow = None
        self.assertEqual({"cow": None}, to_dict.encode_message(a))

        a = Animals()
        a.bird = []
        self.assertEqual({"bird": []}, to_dict.encode_message(a))

        a = Animals()
        a.bird = ["quack", "cheep", "honk"]
        self.assertEqual({"bird": ["quack", "cheep", "honk"]}, to_dict.encode_message(a))

        a = Animals()
        a.cow = "moo"
        a.bird = ["quack", "cheep", "honk"]
        self.assertEqual({"bird": ["quack", "cheep", "honk"], "cow": "moo"}, to_dict.encode_message(a))

    def test_untyped_field_encode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField()

        f = Foo()
        self.assertEqual({}, to_dict.encode_message(f))

        f = Foo()
        f.bar = 123
        self.assertEqual({"bar": 123}, to_dict.encode_message(f))

        f = Foo()
        f.bar = "meow"
        self.assertEqual({"bar": "meow"}, to_dict.encode_message(f))

        f = Foo()
        f.bar = True
        self.assertEqual({"bar": True}, to_dict.encode_message(f))

        f = Foo()
        f.bar = 1.23
        self.assertEqual({"bar": 1.23}, to_dict.encode_message(f))

        f = Foo()
        f.bar = None
        self.assertEqual({"bar": None}, to_dict.encode_message(f))

        f = Foo()
        f.bar = [[123, 1.23, "woof", True], "meow"]
        self.assertEqual({"bar": [[123, 1.23, "woof", True], "meow"]}, to_dict.encode_message(f))

    def test_untyped_field_decode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField()

        f = Foo()
        self.assertEqual(f, to_dict.decode_message(Foo, {}))

        f = Foo()
        f.bar = 123
        self.assertEqual(f, to_dict.decode_message(Foo, {"bar": 123}))

        f = Foo()
        f.bar = "meow"
        self.assertEqual(f, to_dict.decode_message(Foo, {"bar": "meow"}))

        f = Foo()
        f.bar = True
        self.assertEqual(f, to_dict.decode_message(Foo, {"bar": True}))

        f = Foo()
        f.bar = 1.23
        self.assertEqual(f, to_dict.decode_message(Foo, {"bar": 1.23}))

        f = Foo()
        f.bar = 1.23
        self.assertEqual(f, to_dict.decode_message(Foo, {"bar": 1.23}))

        f = Foo()
        f.bar = None
        self.assertEqual(f, to_dict.decode_message(Foo, {"bar": None}))

        f = Foo()
        f.bar = [[123, 1.23, "woof", True], "meow"]
        self.assertEqual(f, to_dict.decode_message(Foo, {"bar": [[123, 1.23, "woof", True], "meow"]}))

    def test_untyped_field_repeated_encode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField(repeated=True)

        f = Foo()
        f.bar = [123, "woof", 1.23, True]
        self.assertEqual({"bar": [123, "woof", 1.23, True]}, to_dict.encode_message(f))

    def test_untyped_field_repeated_decode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField(repeated=True)

        f = Foo()
        f.bar = [123, "woof", 1.23, True]
        self.assertEqual(f, to_dict.decode_message(Foo, {"bar": [123, "woof", 1.23, True]}))

if __name__ == '__main__':
    unittest.main()
