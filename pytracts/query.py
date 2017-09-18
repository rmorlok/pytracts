__author__ = 'Ryan Morlok (ryan@docalytics.com)'
from datetime import datetime

try:
    import iso8601
except ImportError:
    from . import _local_iso8601 as iso8601

from pytracts import messages, to_url, util, exceptions

#
# Decorators used to make handlers more explicit. Enable things like declarative, strongly typed query string parameters.
#

class base_query_parameter(object):
    """
    Base class for decorators that provide query string parameters.
    """
    def __init__(self, name, fself_converter=None, converter=None, validator=None, required=False, default=None, message_missing=None, message_bad_value=None, argument_name=None):
        """
        Creates a new decorator to specify a query parameter that should come into an endpoint call.

        :param name:
            The name of the parameter as it should appear in the query string.

        :param fself_converter:
            A callable that takes the fself object in addition to the value to be converted. Takes precedence over
            the ```converter``` parameter.

        :param converter:
            A callable that can convert a string value to the desired value type (int, array, etc) for
            the parameter value. Only called if the parameter is present.

        :param validator:
            A lambda expression to validate the value of the parameter. Should return true or false to indicate if
            the value is valid. Called with the output of converter, if converter is specified.

        :param required:
            Flag indicating that this query parameter is required. Will raise an HTTPBadRequest exception if not
            present. If not required, None will be passed to the underlying handler.

        :param default:
            The default value returned if the query parameter is not present.

        :param message_missing:
            The message to include if the parameter is missing.

        :param message_bad_value:
            The message to include if the parameter is a bad value.
        """
        self.name = name
        self.argument_name = argument_name or name
        self.fself_converter = fself_converter
        self.converter = converter
        self.validator = validator
        self.required = required
        self.message_missing = message_missing
        self.message_bad_value = message_bad_value
        self.default = default

    def raise_bad_request_value_missing(self):
        raise exceptions.HTTPBadRequest(self.message_missing or ("Required query paramter '%s' is missing." % self.name))

    def raise_bad_request_bad_value(self):
        raise exceptions.HTTPBadRequest(self.message_bad_value or ("Value for parameter '%s' is invalid." % self.name))

    def __call__(self, f):
        """
        Called once to wrap the function in question.
        """
        def wrapper(fself, *arguments, **keywords):
            """
            Called to invoke the actual function.
            """
            param = fself.request.GET.get(self.name)

            if param is None:
                if self.required:
                    self.raise_bad_request_value_missing()
                else:
                    keywords[self.argument_name] = self.default
            else:
                if self.fself_converter is not None:
                    try:
                        param = self.fself_converter(fself, param)
                    except Exception:
                        self.raise_bad_request_bad_value()
                elif self.converter is not None:
                    try:
                        param = self.converter(param)
                    except Exception:
                        self.raise_bad_request_bad_value()
                if self.validator is not None and not self.validator(param):
                    self.raise_bad_request_bad_value()
                keywords[self.argument_name] = param

            # Call the underlying function with parameter added
            return f(fself, *arguments, **keywords)

        return wrapper


class string(base_query_parameter):
    """
    String query parameter.
    """
    pass


class iso8601_date(base_query_parameter):
    """
    Date query parameter formatted according to ISO8601
    """
    def __init__(self, name, validator=None, required=False, message_missing=None, message_bad_value=None, argument_name=None):
        """
        Creates a new decorator to specify a query parameter that should come into an endpoint call.

        :name:
            The name of the parameter as it should appear in the query string.

        :validator:
            A lambda expression to validate the value of the parameter. Should return true or false to indicate if
            the value is valid. Called with the output of converter, if converter is specified.

        :required:
            Flag indicating that this query parameter is required. Will raise an HTTPBadRequest exception if not
            present. If not required, None will be passed to the underlying handler.

        :message:
            The message to include if the parameter is missing or does not pass validation.
        """
        super(iso8601_date, self).__init__(name=name, fself_converter=iso8601_date._parse_date, validator=validator, required=required, message_missing=message_missing, message_bad_value=message_bad_value, argument_name=argument_name)

    @classmethod
    def _parse_date(cls, fself, date_string):
        # Parse the raw date
        dt = iso8601.parse_date(date_string, default_timezone=None)

        if dt.tzinfo is None:
            if hasattr(fself, 'user'):
                if hasattr(fself.user, 'tzinfo') and fself.user.tzinfo is not None:
                    return dt.replace(tzinfo=fself.user.tzinfo)

        return dt


class custom_date(base_query_parameter):
    """
    Date query parameter formatted with a custom date format
    """
    def __init__(self, name, format, validator=None, required=False, message_missing=None, message_bad_value=None, argument_name=None):
        """
        Creates a new decorator to specify a query parameter that should come into an endpoint call.

        :name:
            The name of the parameter as it should appear in the query string.

        :format:
            The format of the date used to parese the date using strptime

        :validator:
            A lambda expression to validate the value of the parameter. Should return true or false to indicate if
            the value is valid. Called with the output of converter, if converter is specified.

        :required:
            Flag indicating that this query parameter is required. Will raise an HTTPBadRequest exception if not
            present. If not required, None will be passed to the underlying handler.

        :message:
            The message to include if the parameter is missing or does not pass validation.
        """
        self.format = format
        super(custom_date, self).__init__(name=name, fself_converter=self._parse_date, validator=validator, required=required, message_missing=message_missing, message_bad_value=message_bad_value, argument_name=argument_name)

    def _parse_date(self, fself, date_string):
        # Parse the raw date
        dt = datetime.strptime(date_string, self.format)

        if dt.tzinfo is None:
            if hasattr(fself, 'user'):
                if hasattr(fself.user, 'tzinfo') and fself.user.tzinfo is not None:
                    return dt.replace(tzinfo=fself.user.tzinfo)

        return dt


class integer(base_query_parameter):
    """
    Integer query parameter
    """
    def __init__(self, name, default=None, validator=None, required=False, message_missing=None, message_bad_value=None, argument_name=None):
        """
        Creates a new decorator to specify a query parameter that should come into an endpoint call.

        :name:
            The name of the parameter as it should appear in the query string.

        :validator:
            A lambda expression to validate the value of the parameter. Should return true or false to indicate if
            the value is valid. Called with the output of converter, if converter is specified.

        :required:
            Flag indicating that this query parameter is required. Will raise an HTTPBadRequest exception if not
            present. If not required, None will be passed to the underlying handler.

        :message:
            The message to include if the parameter is missing or does not pass validation.
        """
        super(integer, self).__init__(name=name, default=default, converter=lambda x: int(x), validator=validator, required=required, message_missing=message_missing, message_bad_value=message_bad_value, argument_name=argument_name)


class boolean(base_query_parameter):
    """
    Boolean query parameter
    """
    def __init__(self, name, default=None, validator=None, required=False, message_missing=None, message_bad_value=None, argument_name=None):
        """
        Creates a new decorator to specify a query parameter that should come into an endpoint call.

        :name:
            The name of the parameter as it should appear in the query string.

        :validator:
            A lambda expression to validate the value of the parameter. Should return true or false to indicate if
            the value is valid. Called with the output of converter, if converter is specified.

        :required:
            Flag indicating that this query parameter is required. Will raise an HTTPBadRequest exception if not
            present. If not required, None will be passed to the underlying handler.

        :message:
            The message to include if the parameter is missing or does not pass validation.
        """
        def _string_to_boolean(value):
            value = value.lower()

            if value == "true":
                return True
            elif value == "false":
                return False
            else:
                raise ValueError("Invalid boolean '%s'" % value)

        super(boolean, self).__init__(name=name, default=default, converter=lambda x: _string_to_boolean(x), validator=validator, required=required, message_missing=message_missing, message_bad_value=message_bad_value, argument_name=argument_name)


class comma_list(base_query_parameter):
    """
    List query parameter. E.g. foo=a,b,c.
    """
    def __init__(self, name, default=None, converter=None, validator=None, required=False, message_missing=None, message_bad_value=None, argument_name=None):
        """
        Creates a new decorator to specify a query parameter that should come into an endpoint call.

        :name:
            The name of the parameter as it should appear in the query string.

        :converter:
            A lambda expression that can convert a string value to the desired value type (int, array, etc) for
            each value in the list. Only called if the parameter is present.

        :validator:
            A lambda expression to validate the value of the parameter. Should return true or false to indicate if
            the value is valid. Called with the output of converter, if converter is specified.

        :required:
            Flag indicating that this query parameter is required. Will raise an HTTPBadRequest exception if not
            present. If not required, None will be passed to the underlying handler.

        :message:
            The message to include if the parameter is missing or does not pass validation.
        """
        super(comma_list, self).__init__(name=name, default=default, converter=lambda lst: [converter(x) for x in lst.split(',')] if converter is not None else lst.split(','), validator=validator, required=required, message_missing=message_missing, message_bad_value=message_bad_value, argument_name=argument_name)


class integer_list(comma_list):
    """
    Integer list query parameter. E.g. foo=1,2,3
    """
    def __init__(self, name, default=None, validator=None, required=False, message_missing=None, message_bad_value=None, argument_name=None):
        """
        Creates a new decorator to specify a query parameter that should come into an endpoint call.

        :name:
            The name of the parameter as it should appear in the query string.

        :validator:
            A lambda expression to validate the value of the parameter. Should return true or false to indicate if
            the value is valid. Called with the output of converter, if converter is specified.

        :required:
            Flag indicating that this query parameter is required. Will raise an HTTPBadRequest exception if not
            present. If not required, None will be passed to the underlying handler.

        :message:
            The message to include if the parameter is missing or does not pass validation.
        """
        super(integer_list, self).__init__(name=name, default=default, converter=lambda x: int(x), validator=validator, required=required, message_missing=message_missing, message_bad_value=message_bad_value, argument_name=argument_name)


def message(*args, **kwargs):
    """
    Decorator that allows an endpoint to use pytracts messages for the query parameters.
    """

    if len(kwargs) > 1:
        raise IndexError("Cannot have more than one mapping for query parameter message")

    if len(args) > 1:
        raise IndexError("Cannot have more than one mapping for query parameter message")

    if len(args) >= 1 and len(kwargs) >= 1:
        raise IndexError("Cannot specify both a named parameter and a positional parameter")

    if len(kwargs) == 1:
        message_param_name = kwargs.keys()[0]
        message_param_type = kwargs.values()[0]
    elif len(args) == 1:
        message_param_name = None
        message_param_type = args[0]
    else:
        raise IndexError("Must specify query parameter message type")

    if not isinstance(message_param_type, messages.Message):
        raise TypeError("Message must be of type pytracts.messages.Message")

    def get_wrapper(message_param_name, message_param_type, f):
        def wrapper(self, *arguments, **keywords):
            try:
                m = to_url.decode_message_from_url(message_type=message_param_type, url=self.request.url)

                if message_param_name:
                    keywords[message_param_name] = m
                else:
                    arguments += (m,)

            except (ValueError, messages.Error) as error:
                raise exceptions.HTTPBadRequest(detail=(error.message or "Could not decode query parameters"))

            return f(self, *arguments, **keywords)

        return wrapper

    return util.curry(get_wrapper, message_param_name, message_param_type)
