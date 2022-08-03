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

"""
dictionary support for message types.

Public functions:
  encode_message: Encodes a message in to a dictionary.
  decode_message: Merge from a dictionary in to a message.
"""

__author__ = 'ryan.morlok@morlok.com (Ryan Morlok)'

import sys
import logging

from . import messages

__all__ = [
    'encode_message',
    'decode_message',
    'decode_dictionary',
]

if sys.version_info >= (3, 0, 0):
    unicode = str
    basestring = str
    long = int

    def cmp(a, b):
        return (a > b) - (a < b)

def __encode_value(value):
    if isinstance(value, messages.Enum):
        return str(value)

    if isinstance(value, messages.Message):
        result = {}
        for field in value.all_fields():
            if value.has_value_assigned(field.name):
                item = value.get_assigned_value(field.name)
                if field.repeated:
                    result[field.name] = [__encode_value(v) for v in item]
                else:
                    result[field.name] = __encode_value(item)

        # Handle unrecognized fields, so they're included when a message is decoded then encoded.
        for unknown_key in value.all_unrecognized_fields():
            unrecognized_field, _ = value.get_unrecognized_field_info(unknown_key)
            result[unknown_key] = unrecognized_field

        return result

    return value


def encode_message(message):
    """
    Encode Message instance to a dictionary.

    :param message: Message instance to encode in to a dictionary.

    :returns:
      a dictionary version of the message.

    :raises:
      messages.ValidationError if message is not initialized.
    """
    if not isinstance(message, messages.Message):
        raise TypeError("Object must be of type message")

    message.check_initialized()

    return __encode_value(message)


def __find_variant(value):
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
            variant = __find_variant(v)
            try:
                priority = variant_priority.index(variant)
            except IndexError:
                priority = -1
            if priority > chosen_priority:
                chosen_priority = priority
        return variant_priority[chosen_priority]
    # Unrecognized type.
    return None


def decode_dictionary(message_type, dictionary):
    """
    Merge dictionary in to message.

    :param message: Message to merge dictionary in to.
    :param dictionary: Dictionary to extract information from. Nested objects will also be dictionaries.
    """
    message = message_type()
    try:
        for key, value in dictionary.items():
            try:
                field = message.field_by_name(key)
            except KeyError:
                # Save unknown values.
                variant = __find_variant(value)
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
                    valid_value.append(__decode_field(field, item))

                if field.repeated:
                    existing_value = getattr(message, field.alias)
                    setattr(message, field.alias, valid_value)
                else:
                    setattr(message, field.alias, valid_value[-1])

        return message

    except AttributeError:
        raise ValueError("Decoded value must be of type dict")


# Decode message is just an alias for decode dictionary
decode_message = decode_dictionary


def __decode_field(field, value):
    if value is None:
        return None

    elif isinstance(field, messages.EnumField):
        try:
            return field.type(value)
        except TypeError:
            raise messages.DecodeError('Invalid enum value "%s"' % value[0])

    elif (isinstance(field, messages.MessageField) and
              issubclass(field.type, messages.Message)):
        return decode_dictionary(field.type, value)

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
