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

"""Tests for protopy.protojson."""
from tests import test_util

__author__ = 'rafek@google.com (Rafe Kaplan)'

import datetime
import sys
import unittest

from protopy import message_types
from protopy import messages
from protopy import protojson

import json


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
    a_datetime = message_types.DateTimeField()
    a_repeated_datetime = message_types.DateTimeField(repeated=True)
    a_custom = CustomField()
    a_repeated_custom = CustomField(repeated=True)


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):
    MODULE = protojson


# TODO(rafek): Convert this test to the compliance test in test_util.
class ProtojsonTest(test_util.TestCase,
                    test_util.ProtoConformanceTestBase):
    """Test JSON encoding and decoding."""

    PROTOLIB = protojson

    def CompareEncoded(self, expected_encoded, actual_encoded):
        """JSON encoding will be laundered to remove string differences."""
        self.assertEquals(json.loads(expected_encoded),
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
        message = protojson.decode_message(MyMessage, '{"a_float": 10}')

        self.assertTrue(isinstance(message.a_float, float))
        self.assertEquals(10.0, message.a_float)

    def testConvertStringToNumbers(self):
        """Test that strings passed to integer fields are converted."""
        message = protojson.decode_message(MyMessage,
                                           """{"an_integer": "10",
                                               "a_float": "3.5",
                                               "a_repeated": ["1", "2"],
                                               "a_repeated_float": ["1.5", "2", 10]
                                               }""")

        self.assertEquals(MyMessage(an_integer=10,
                                    a_float=3.5,
                                    a_repeated=[1, 2],
                                    a_repeated_float=[1.5, 2.0, 10.0]),
                          message)

    def testWrongTypeAssignment(self):
        """Test when wrong type is assigned to a field."""
        self.assertRaises(messages.ValidationError,
                          protojson.decode_message,
                          MyMessage, '{"a_string": 10}')
        self.assertRaises(messages.ValidationError,
                          protojson.decode_message,
                          MyMessage, '{"an_integer": 10.2}')
        self.assertRaises(messages.ValidationError,
                          protojson.decode_message,
                          MyMessage, '{"an_integer": "10.2"}')

    def testNumericEnumeration(self):
        """Test that numbers work for enum values."""
        message = protojson.decode_message(MyMessage, '{"an_enum": 2}')

        expected_message = MyMessage()
        expected_message.an_enum = MyMessage.Color.GREEN

        self.assertEquals(expected_message, message)

    def testNullValues(self):
        """Test that null values overwrite existing values."""
        m = MyMessage()
        m.an_integer = None
        m.a_nested = None

        self.assertEquals(m,
                          protojson.decode_message(MyMessage,
                                                   ('{"an_integer": null,'
                                                    ' "a_nested": null'
                                                    '}')))

    def testEmptyList(self):
        """Test that empty lists are not ignored."""
        m = MyMessage()
        m.a_repeated = []
        self.assertEquals(m,
                          protojson.decode_message(MyMessage,
                                                   '{"a_repeated": []}'))

    def testNotJSON(self):
        """Test error when string is not valid JSON."""
        self.assertRaises(ValueError,
                          protojson.decode_message, MyMessage, '{this is not json}')

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
                          protojson.encode_message,
                          BogusObject())

    def testMergeEmptyString(self):
        """Test merging the empty or space only string."""
        message = protojson.decode_message(test_util.OptionalMessage, '')
        self.assertEquals(test_util.OptionalMessage(), message)

        message = protojson.decode_message(test_util.OptionalMessage, ' ')
        self.assertEquals(test_util.OptionalMessage(), message)

    def testProtojsonUnrecognizedFieldName(self):
        """Test that unrecognized fields are saved and can be accessed."""
        decoded = protojson.decode_message(MyMessage,
                                           ('{"an_integer": 1, "unknown_val": 2}'))
        self.assertEquals(decoded.an_integer, 1)
        self.assertEquals(1, len(decoded.all_unrecognized_fields()))
        self.assertEquals('unknown_val', decoded.all_unrecognized_fields()[0])
        self.assertEquals((2, messages.Variant.INT64),
                          decoded.get_unrecognized_field_info('unknown_val'))

    def testProtojsonUnrecognizedFieldNumber(self):
        """Test that unrecognized fields are saved and can be accessed."""
        decoded = protojson.decode_message(
            MyMessage,
            '{"an_integer": 1, "1001": "unknown", "-123": "negative", '
            '"456_mixed": 2}')
        self.assertEquals(decoded.an_integer, 1)
        self.assertEquals(3, len(decoded.all_unrecognized_fields()))
        self.assertIn(1001, decoded.all_unrecognized_fields())
        self.assertEquals(('unknown', messages.Variant.STRING),
                          decoded.get_unrecognized_field_info(1001))
        self.assertIn('-123', decoded.all_unrecognized_fields())
        self.assertEquals(('negative', messages.Variant.STRING),
                          decoded.get_unrecognized_field_info('-123'))
        self.assertIn('456_mixed', decoded.all_unrecognized_fields())
        self.assertEquals((2, messages.Variant.INT64),
                          decoded.get_unrecognized_field_info('456_mixed'))

    def testProtojsonUnrecognizedNull(self):
        """Test that unrecognized fields that are None are skipped."""
        decoded = protojson.decode_message(
            MyMessage,
            '{"an_integer": 1, "unrecognized_null": null}')
        self.assertEquals(decoded.an_integer, 1)
        self.assertEquals(decoded.all_unrecognized_fields(), [])

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
            decoded = protojson.decode_message(MyMessage, encoded)
            self.assertEquals(decoded.an_integer, 1)
            self.assertEquals(1, len(decoded.all_unrecognized_fields()))
            self.assertEquals('unknown_val', decoded.all_unrecognized_fields()[0])
            _, decoded_variant = decoded.get_unrecognized_field_info('unknown_val')
            self.assertEquals(expected_variant, decoded_variant)

    def testDecodeDateTime(self):
        for datetime_string, datetime_vals in (
                ('2012-09-30T15:31:50.262', (2012, 9, 30, 15, 31, 50, 262000)),
                ('2012-09-30T15:31:50', (2012, 9, 30, 15, 31, 50, 0))):
            message = protojson.decode_message(
                MyMessage, '{"a_datetime": "%s"}' % datetime_string)
            expected_message = MyMessage(
                a_datetime=datetime.datetime(*datetime_vals))

            self.assertEquals(expected_message, message)

    def testDecodeInvalidDateTime(self):
        self.assertRaises(messages.DecodeError, protojson.decode_message,
                          MyMessage, '{"a_datetime": "invalid"}')

    def testEncodeDateTime(self):
        for datetime_string, datetime_vals in (
                ('2012-09-30T15:31:50.262000', (2012, 9, 30, 15, 31, 50, 262000)),
                ('2012-09-30T15:31:50.262123', (2012, 9, 30, 15, 31, 50, 262123)),
                ('2012-09-30T15:31:50', (2012, 9, 30, 15, 31, 50, 0))):
            decoded_message = protojson.encode_message(
                MyMessage(a_datetime=datetime.datetime(*datetime_vals)))
            expected_decoding = '{"a_datetime": "%s"}' % datetime_string
            self.CompareEncoded(expected_decoding, decoded_message)

    def testDecodeRepeatedDateTime(self):
        message = protojson.decode_message(
            MyMessage,
            '{"a_repeated_datetime": ["2012-09-30T15:31:50.262", '
            '"2010-01-21T09:52:00", "2000-01-01T01:00:59.999999"]}')
        expected_message = MyMessage(
            a_repeated_datetime=[
                datetime.datetime(2012, 9, 30, 15, 31, 50, 262000),
                datetime.datetime(2010, 1, 21, 9, 52),
                datetime.datetime(2000, 1, 1, 1, 0, 59, 999999)])

        self.assertEquals(expected_message, message)

    def testDecodeCustom(self):
        message = protojson.decode_message(MyMessage, '{"a_custom": 1}')
        self.assertEquals(MyMessage(a_custom=1), message)

    def testDecodeInvalidCustom(self):
        self.assertRaises(messages.ValidationError, protojson.decode_message,
                          MyMessage, '{"a_custom": "invalid"}')

    def testEncodeCustom(self):
        decoded_message = protojson.encode_message(MyMessage(a_custom=1))
        self.CompareEncoded('{"a_custom": 1}', decoded_message)

    def testDecodeRepeatedCustom(self):
        message = protojson.decode_message(
            MyMessage, '{"a_repeated_custom": [1, 2, 3]}')
        self.assertEquals(MyMessage(a_repeated_custom=[1, 2, 3]), message)

    def testDecodeBadBase64BytesField(self):
        """Test decoding improperly encoded base64 bytes value."""
        self.assertRaisesWithRegexpMatch(
            messages.DecodeError,
            'Base64 decoding error: Incorrect padding',
            protojson.decode_message,
            test_util.OptionalMessage,
            '{"bytes_value": "abcdefghijklmnopq"}')

    def test_has_value_assigned(self):
        class Foo(messages.Message):
            not_set = messages.StringField()
            set_null = messages.StringField()

        message = protojson.decode_message(Foo, '{"set_null": null}')
        self.assertFalse(message.has_value_assigned('not_set'))
        self.assertTrue(message.has_value_assigned('set_null'))
        self.assertIsNone(message.not_set)
        self.assertIsNone(message.set_null)

    def test_has_value_assigned_repeated(self):
        class Foo(messages.Message):
            pete = messages.StringField(repeated=True)

        message = protojson.decode_message(Foo, '{"pete": []}')
        self.assertTrue(message.has_value_assigned('pete'))

        message = protojson.decode_message(Foo, '{"pete": ["sat"]}')
        self.assertTrue(message.has_value_assigned('pete'))

        message = protojson.decode_message(Foo, '{"pete": ["sat", "in", "a", "boat"]}')
        self.assertTrue(message.has_value_assigned('pete'))

    def test_repeated_value_null_not_allowed(self):
        class Foo(messages.Message):
            pete = messages.StringField(repeated=True)

        self.assertRaises(messages.ValidationError, lambda: protojson.decode_message(Foo, '{"pete": null}'))

    def test_explicit_field_name(self):
        class Foo(messages.Message):
            bob = messages.StringField(name="robert")
            ryan = messages.StringField()

        m = protojson.decode_message(Foo, '{"robert": "smith", "ryan": "morlok"}')

        self.assertEquals("smith", m.bob)
        self.assertEquals("morlok", m.ryan)

        f = Foo()
        f.bob = "smith"
        f.ryan = "morlok"

        self.assertEquals('{"robert": "smith", "ryan": "morlok"}', protojson.encode_message(f))

    def test_assigned_values_rendered(self):
        class Animals(messages.Message):
            bird = messages.StringField(repeated=True)
            cow = messages.StringField()

        a = Animals()
        self.assertEquals('{}', protojson.encode_message(a))

        a = Animals()
        a.cow = "moo"
        self.assertEquals('{"cow": "moo"}', protojson.encode_message(a))

        a = Animals()
        a.cow = None
        self.assertEquals('{"cow": null}', protojson.encode_message(a))

        a = Animals()
        a.bird = []
        self.assertEquals('{"bird": []}', protojson.encode_message(a))

        a = Animals()
        a.bird = ["quack", "cheep", "honk"]
        self.assertEquals('{"bird": ["quack", "cheep", "honk"]}', protojson.encode_message(a))

        a = Animals()
        a.cow = "moo"
        a.bird = ["quack", "cheep", "honk"]
        self.assertEquals('{"bird": ["quack", "cheep", "honk"], "cow": "moo"}', protojson.encode_message(a))

    def test_untyped_field_encode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField()

        f = Foo()
        self.assertEquals('{}', protojson.encode_message(f))

        f = Foo()
        f.bar = 123
        self.assertEquals('{"bar": 123}', protojson.encode_message(f))

        f = Foo()
        f.bar = "meow"
        self.assertEquals('{"bar": "meow"}', protojson.encode_message(f))

        f = Foo()
        f.bar = True
        self.assertEquals('{"bar": true}', protojson.encode_message(f))

        f = Foo()
        f.bar = 1.23
        self.assertEquals('{"bar": 1.23}', protojson.encode_message(f))

    def test_untyped_field_decode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField()

        f = Foo()
        self.assertEquals(f, protojson.decode_message(Foo, '{}'))

        f = Foo()
        f.bar = 123
        self.assertEquals(f, protojson.decode_message(Foo, '{"bar": 123}'))

        f = Foo()
        f.bar = "meow"
        self.assertEquals(f, protojson.decode_message(Foo, '{"bar": "meow"}'))

        f = Foo()
        f.bar = True
        self.assertEquals(f, protojson.decode_message(Foo, '{"bar": true}'))

        f = Foo()
        f.bar = 1.23
        self.assertEquals(f, protojson.decode_message(Foo, '{"bar": 1.23}'))

    def test_untyped_field_repeated_encode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField(repeated=True)

        f = Foo()
        f.bar = [123, "woof", 1.23, True]
        self.assertEquals('{"bar": [123, "woof", 1.23, true]}', protojson.encode_message(f))

    def test_untyped_field_repeated_decode(self):
        class Foo(messages.Message):
            bar = messages.UntypedField(repeated=True)

        f = Foo()
        f.bar = [123, "woof", 1.23, True]
        self.assertEquals(f, protojson.decode_message(Foo, '{"bar": [123, "woof", 1.23, true]}'))

    def test_dict_field_encode(self):
        class GrabBag(messages.Message):
            item_count = messages.IntegerField()
            items = messages.DictField()

        gb = GrabBag()
        self.assertEquals('{}', protojson.encode_message(gb))

        gb = GrabBag()
        gb.item_count = 123
        self.assertEquals('{"item_count": 123}', protojson.encode_message(gb))

        gb = GrabBag()
        gb.item_count = 123
        gb.items = {}
        self.assertEquals('{"items": {}, "item_count": 123}', protojson.encode_message(gb))

        gb = GrabBag()
        gb.item_count = 123
        gb.items = {'a': 'b', 'foo': 'bar'}
        self.assertEquals('{"items": {"a": "b", "foo": "bar"}, "item_count": 123}', protojson.encode_message(gb))

    def test_dict_field_decode(self):
        class GrabBag(messages.Message):
            item_count = messages.IntegerField()
            items = messages.DictField()

        gb = GrabBag()
        self.assertEquals(gb, protojson.decode_message(GrabBag, '{}'))

        gb = GrabBag()
        gb.item_count = 123
        self.assertEquals(gb, protojson.decode_message(GrabBag, '{"item_count": 123}'))

        gb = GrabBag()
        gb.item_count = 123
        gb.items = {}
        self.assertEquals(gb, protojson.decode_message(GrabBag, '{"items": {}, "item_count": 123}'))

        gb = GrabBag()
        gb.item_count = 123
        gb.items = {'a': 'b', 'foo': 'bar'}
        self.assertEquals(gb, protojson.decode_message(GrabBag, '{"items": {"a": "b", "foo": "bar"}, "item_count": 123}'))


class CustomProtoJson(protojson.ProtoJson):
    def encode_field(self, field, value):
        return '{encoded}' + value

    def decode_field(self, field, value):
        return '{decoded}' + value


class CustomProtoJsonTest(test_util.TestCase):
    """Tests for serialization overriding functionality."""

    def setUp(self):
        self.protojson = CustomProtoJson()

    def testEncode(self):
        self.assertEqual('{"a_string": "{encoded}xyz"}', self.protojson.encode_message(MyMessage(a_string='xyz')))

    def testDecode(self):
        self.assertEqual(
            MyMessage(a_string='{decoded}xyz'),
            self.protojson.decode_message(MyMessage, '{"a_string": "xyz"}'))

    def testDefault(self):
        self.assertTrue(protojson.ProtoJson.get_default(),
                        protojson.ProtoJson.get_default())

        instance = CustomProtoJson()
        protojson.ProtoJson.set_default(instance)
        self.assertTrue(instance is protojson.ProtoJson.get_default())


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
        reload(protojson)

    def testLoadProtojsonWithValidJsonModule(self):
        """Test loading protojson module with a valid json dependency."""
        sys.modules['json'] = ValidJsonModule

        # This will cause protojson to reload with the default json module
        # instead of simplejson.
        reload(protojson)
        self.assertEquals('json', protojson.json.name)

    def testLoadProtojsonWithSimplejsonModule(self):
        """Test loading protojson module with simplejson dependency."""
        sys.modules['simplejson'] = ValidJsonModule

        # This will cause protojson to reload with the default json module
        # instead of simplejson.
        reload(protojson)
        self.assertEquals('simplejson', protojson.json.name)

    def testLoadProtojsonWithInvalidJsonModule(self):
        """Loading protojson module with an invalid json defaults to simplejson."""
        sys.modules['json'] = InvalidJsonModule
        sys.modules['simplejson'] = ValidJsonModule

        # Ignore bad module and default back to simplejson.
        reload(protojson)
        self.assertEquals('simplejson', protojson.json.name)

    def testLoadProtojsonWithInvalidJsonModuleAndNoSimplejson(self):
        """Loading protojson module with invalid json and no simplejson."""
        sys.modules['json'] = InvalidJsonModule

        # Bad module without simplejson back raises errors.
        self.assertRaisesWithRegexpMatch(
            ImportError,
            'json library "json" is not compatible with ProtoPy',
            reload,
            protojson)

    def testLoadProtojsonWithNoJsonModules(self):
        """Loading protojson module with invalid json and no simplejson."""
        # No json modules raise the first exception.
        self.assertRaisesWithRegexpMatch(
            ImportError,
            'Unable to find json',
            reload,
            protojson)


if __name__ == '__main__':
    unittest.main()
