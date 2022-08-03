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

"""JSON support for message types.

Public classes:
  MessageJSONEncoder: JSON encoder for message objects.

Public functions:
  encode_message: Encodes a message in to a JSON string.
  decode_message: Merge from a JSON string in to a message.
"""

__author__ = 'rafek@google.com (Rafe Kaplan)'

import sys
import base64
import logging
import datetime
import binascii
import uuid

try:
    import iso8601
except ImportError:
    from . import _local_iso8601 as iso8601

from . import message_types
from . import messages
from . import util

__all__ = [
    'ALTERNATIVE_CONTENT_TYPES',
    'CONTENT_TYPE',
    'MessageJSONEncoder',
    'encode_message',
    'decode_message',
    'JsonEncoder',
]

if sys.version_info >= (3, 0, 0):
    unicode = str
    basestring = str
    long = int

    def cmp(a, b):
        return (a > b) - (a < b)


def _load_json_module():
    """Try to load a valid json module.

    There are more than one json modules that might be installed.  They are
    mostly compatible with one another but some versions may be different.
    This function attempts to load various json modules in a preferred order.
    It does a basic check to guess if a loaded version of json is compatible.

    Returns:
      Compatible json module.

    Raises:
      ImportError if there are no json modules or the loaded json module is
        not compatible with ProtoPy.
    """
    first_import_error = None
    for module_name in ['json',
                        'simplejson']:
        try:
            module = __import__(module_name, {}, {}, 'json')
            if not hasattr(module, 'JSONEncoder'):
                message = ('json library "%s" is not compatible with ProtoPy' %
                           module_name)
                logging.warning(message)
                raise ImportError(message)
            else:
                return module
        except ImportError as err:
            if not first_import_error:
                first_import_error = err

    logging.error('Must use valid json library (Python 2.6 json or simplejson)')
    raise first_import_error


json = _load_json_module()


# TODO: Rename this to MessageJsonEncoder.
class MessageJSONEncoder(json.JSONEncoder):
    """Message JSON encoder class.

    Extension of JSONEncoder that can build JSON from a message object.
    """

    def __init__(self, to_json_protocol=None, **kwargs):
        """Constructor.

        Args:
          to_json_protocol: ProtoJson instance.
        """
        super(MessageJSONEncoder, self).__init__(**kwargs)
        self.__to_json_protocol = to_json_protocol or JsonEncoder.get_default()

    def default(self, value):
        """
        Return dictionary instance from a message object.

        :param value: Value to get dictionary for.  If not encodable, will call superclasses default method.

        :returns the value as a dictionary
        """
        if isinstance(value, messages.Enum):
            return str(value)

        if isinstance(value, messages.Message):
            result = {}
            for field in value.all_fields():
                if value.has_value_assigned(field.name):
                    item = value.get_assigned_value(field.name)
                    result[field.name] = self.__to_json_protocol.encode_field(field, item)

            # Handle unrecognized fields, so they're included when a message is decoded then encoded.
            for unknown_key in value.all_unrecognized_fields():
                unrecognized_field, _ = value.get_unrecognized_field_info(unknown_key)
                result[unknown_key] = unrecognized_field
            return result
        else:
            return super(MessageJSONEncoder, self).default(value)


class JsonEncoder(object):
    """
    Pytracts JSON implementation class.

    Implementation of JSON based protocol used for serializing and deserializing
    message objects.  Instances of remote.ProtocolConfig constructor or used with
    remote.Protocols.add_protocol.  See the remote.py module for more details.
    """

    CONTENT_TYPE = 'application/json'
    ALTERNATIVE_CONTENT_TYPES = [
        'application/x-javascript',
        'text/javascript',
        'text/x-javascript',
        'text/x-json',
        'text/json',
    ]

    def prep_dict(self, d):
        """
        Prepare a dictionary for encoding by making sure non-json serializable types that
        we know how to handle are converted.

        :param d: the dict

        :return: the updated dict
        """
        if d is None:
            return None

        d = d.copy()

        for key in d.keys():
            if isinstance(d[key], datetime.datetime) or isinstance(d[key], datetime.date) or isinstance(d[key], datetime.time):
                d[key] = d[key].isoformat()
            if isinstance(d[key], dict):
                d[key] = self.prep_dict(d[key])

        return d

    def encode_field(self, field, value):
        """
        Encode a python field value to a JSON value.

        :param field: A ProtoPy field instance.
        :param value: A python value supported by field.

        Returns:
          A JSON serializable value appropriate for field.
        """
        if isinstance(field, messages.BytesField):
            if field.repeated:
                value = [base64.b64encode(byte).decode("utf-8") for byte in value]
            else:
                value = base64.b64encode(value).decode("utf-8")
        elif isinstance(field, messages.DateTimeISO8601Field):
            # DateTimeField stores its data as a ISO 8601 compliant string.
            if field.repeated:
                value = [i.isoformat() for i in value]
            else:
                value = value.isoformat()
        elif isinstance(field, messages.DateTimeMsIntegerField):
            # DateTimeField stores its data as a ISO 8601 compliant string.
            if field.repeated:
                value = [util.datetime_to_ms(i) for i in value]
            else:
                value = util.datetime_to_ms(value)
        elif isinstance(field, messages.UUIDField):
            if field.repeated:
                value = [str(uuid) for uuid in value]
            else:
                value = str(value)
        elif isinstance(field, messages.DictField):
            value = self.prep_dict(value)

        return value

    def encode_message(self, message):
        """Encode Message instance to JSON string.

        Args:
          Message instance to encode in to JSON string.

        Returns:
          String encoding of Message instance in protocol JSON format.

        Raises:
          messages.ValidationError if message is not initialized.
        """
        message.check_initialized()

        return json.dumps(message, cls=MessageJSONEncoder, to_json_protocol=self)

    def decode_message(self, message_type, encoded_message):
        """Merge JSON structure to Message instance.

        Args:
          message_type: Message to decode data to.
          encoded_message: JSON encoded version of message.

        Returns:
          Decoded instance of message_type.

        Raises:
          ValueError: If encoded_message is not valid JSON.
          messages.ValidationError if merged message is not initialized.
        """
        if not encoded_message.strip():
            return message_type()

        dictionary = json.loads(encoded_message)
        message = self.__decode_dictionary(message_type, dictionary)
        message.check_initialized()
        return message

    def __find_variant(self, value):
        """Find the messages.Variant type that describes this value.

        Args:
          value: The value whose variant type is being determined.

        Returns:
          The messages.Variant value that best describes value's type, or None if
          it's a type we don't know how to handle.
        """
        if isinstance(value, bool):
            return messages.Variant.BOOL
        elif isinstance(value, (int, long)):
            return messages.Variant.INT64
        elif isinstance(value, float):
            return messages.Variant.DOUBLE
        elif isinstance(value, basestring):
            return messages.Variant.STRING
        elif isinstance(value, (list, tuple)):
            # Find the most specific variant that covers all elements.
            variant_priority = [None, messages.Variant.INT64, messages.Variant.DOUBLE,
                                messages.Variant.STRING]
            chosen_priority = 0
            for v in value:
                variant = self.__find_variant(v)
                try:
                    priority = variant_priority.index(variant)
                except IndexError:
                    priority = -1
                if priority > chosen_priority:
                    chosen_priority = priority
            return variant_priority[chosen_priority]
        # Unrecognized type.
        return None

    def __decode_dictionary(self, message_type, dictionary):
        """Merge dictionary in to message.

        Args:
          message: Message to merge dictionary in to.
          dictionary: Dictionary to extract information from.  Dictionary
            is as parsed from JSON.  Nested objects will also be dictionaries.
        """
        message = message_type()
        for key, value in dictionary.items():
            try:
                field = message.field_by_name(key)
            except KeyError:
                # Save unknown values.
                variant = self.__find_variant(value)
                if variant:
                    if key.isdigit():
                        key = int(key)
                    message.set_unrecognized_field(key, value, variant)
                else:
                    logging.warning('No variant found for unrecognized field: %s', key)
                continue

            # Special case untyped fields to allow the data to flow right in
            if isinstance(field, messages.UntypedField):
                setattr(message, field.alias, value)
            else:
                # Normalize values in to a list.
                if not isinstance(value, list):
                    value = [value]

                valid_value = []
                for item in value:
                    valid_value.append(self.decode_field(field, item))

                if field.repeated:
                    existing_value = getattr(message, field.name)
                    setattr(message, field.alias, valid_value)
                else:
                    setattr(message, field.alias, valid_value[-1])

        return message

    def decode_field(self, field, value):
        """Decode a JSON value to a python value.

        Args:
          field: A pytract field instance.
          value: A serialized JSON value.

        Return:
          A Python value compatible with field.
        """
        if value is None:
            return None

        elif isinstance(field, messages.EnumField):
            try:
                return field.type(value)
            except TypeError:
                raise messages.DecodeError('Invalid enum value "%s"' % value[0])

        elif isinstance(field, messages.BytesField):
            try:
                return base64.b64decode(value)
            except TypeError as err:
                raise messages.DecodeError('Base64 decoding error: %s' % err)
            except binascii.Error as err:
                raise messages.DecodeError('Base64 decoding error: %s' % err)

        elif isinstance(field, messages.DateTimeISO8601Field):
            try:
                return iso8601.parse_date(value, default_timezone=None)
            except iso8601.ParseError as err:
                raise messages.DecodeError('iso8601 decoding error: %s' % err)

        elif isinstance(field, messages.DateTimeMsIntegerField):
            try:
                return util.ms_to_datetime(value)
            except TypeError as err:
                raise messages.DecodeError('datetime decoding error: %s' % err)
            except ValueError as err:
                raise messages.DecodeError('datetime decoding error: %s' % err)

        elif isinstance(field, messages.UUIDField):
            try:
                return uuid.UUID(value)
            except TypeError as err:
                raise messages.DecodeError('uuid decoding error: %s' % err)
            except ValueError as err:
                raise messages.DecodeError('uuid decoding error: %s' % err)

        elif (isinstance(field, messages.MessageField) and
                  issubclass(field.type, messages.Message)):
            return self.__decode_dictionary(field.type, value)

        elif (isinstance(field, messages.FloatField) and
                  isinstance(value, (int, long, basestring))):
            try:
                return float(value)
            except:
                pass

        elif (isinstance(field, messages.IntegerField) and
                  isinstance(value, basestring)):
            try:
                return int(value)
            except:
                pass

        return value

    @staticmethod
    def get_default():
        """Get default instanceof to_json."""
        try:
            return JsonEncoder.__default
        except AttributeError:
            JsonEncoder.__default = JsonEncoder()
            return JsonEncoder.__default

    @staticmethod
    def set_default(protocol):
        """Set the default instance of ProtoJson.

        Args:
          protocol: A ProtoJson instance.
        """
        if not isinstance(protocol, JsonEncoder):
            raise TypeError('Expected protocol of type Pytracts')
        JsonEncoder.__default = protocol


CONTENT_TYPE = JsonEncoder.CONTENT_TYPE

ALTERNATIVE_CONTENT_TYPES = JsonEncoder.ALTERNATIVE_CONTENT_TYPES

encode_message = JsonEncoder.get_default().encode_message

decode_message = JsonEncoder.get_default().decode_message
