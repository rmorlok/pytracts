__all__ = [
    "HTTPBaseException",
    "HTTPBadRequest",
    "HTTPUnauthorized",
    "HTTPForbidden",
    "HTTPNotFound",
    "HTTPMethodNotAllowed",
    "HTTPNotAcceptable",
    "HTTPRequestTimeout",
    "HTTPConflict",
    "HTTPGone",
    "HTTPLengthRequired",
    "HTTPPreconditionFailed",
    "HTTPRequestEntityTooLarge",
    "HTTPRequestURITooLarge",
    "HTTPUnsupportedMediaType",
    "HTTPRequestedRangeNotSatisfiable",
    "HTTPExpectationFailed",
    "HTTPImATeapot",
    "HTTPUnprocessableEntity",
    "HTTPLocked",
    "HTTPPreconditionRequired",
    "HTTPTooManyRequests",
    "HTTPRequestHeaderFieldsTooLarge",
    "HTTPUnavailableForLegalReasons",
    "HTTPInternalServerError",
    "HTTPNotImplemented",
    "HTTPBadGateway",
    "HTTPServiceUnavailable",
    "HTTPGatewayTimeout",
    "HTTPHTTPVersionNotSupported",
]


try:
    from webob import exc


    class _HTTPImATeapot(exc.HTTPClientError):
        """
        subclass of :class:`~HTTPClientError`

        I'm a teapot status code.

        code: 418, title: I'm a teapot
        """
        code = 418
        title = "I'm a teapot"
        explanation = ("I'm a teapot")

    HTTPBaseException = exc.HTTPException

    # 400s
    HTTPBadRequest = exc.HTTPBadRequest
    HTTPUnauthorized = exc.HTTPUnauthorized
    HTTPForbidden = exc.HTTPForbidden
    HTTPNotFound = exc.HTTPNotFound
    HTTPMethodNotAllowed = exc.HTTPMethodNotAllowed
    HTTPNotAcceptable = exc.HTTPNotAcceptable
    HTTPRequestTimeout = exc.HTTPRequestTimeout
    HTTPConflict = exc.HTTPConflict
    HTTPGone = exc.HTTPGone
    HTTPLengthRequired = exc.HTTPLengthRequired
    HTTPPreconditionFailed = exc.HTTPPreconditionFailed
    HTTPRequestEntityTooLarge = exc.HTTPRequestEntityTooLarge
    HTTPRequestURITooLarge = exc.HTTPRequestURITooLong
    HTTPUnsupportedMediaType = exc.HTTPUnsupportedMediaType
    HTTPRequestedRangeNotSatisfiable = exc.HTTPRequestRangeNotSatisfiable
    HTTPExpectationFailed = exc.HTTPExpectationFailed
    HTTPImATeapot = _HTTPImATeapot
    HTTPUnprocessableEntity = exc.HTTPUnprocessableEntity
    HTTPLocked = exc.HTTPLocked
    HTTPPreconditionRequired = exc.HTTPPreconditionRequired
    HTTPTooManyRequests = exc.HTTPTooManyRequests
    HTTPRequestHeaderFieldsTooLarge = exc.HTTPRequestHeaderFieldsTooLarge
    HTTPUnavailableForLegalReasons = exc.HTTPUnavailableForLegalReasons

    # 500s
    HTTPInternalServerError = exc.HTTPInternalServerError
    HTTPNotImplemented = exc.HTTPNotImplemented
    HTTPBadGateway = exc.HTTPBadGateway
    HTTPServiceUnavailable = exc.HTTPServiceUnavailable
    HTTPGatewayTimeout = exc.HTTPGatewayTimeout
    HTTPHTTPVersionNotSupported = exc.HTTPVersionNotSupported
except ImportError:
    pass

try:
    from werkzeug import exceptions as exc

    HTTPBaseException = exc.HTTPException


    class _Locked(exc.HTTPException):

        """*423* `Locked`

        Used if the resource that is being accessed is locked.
        """
        code = 423
        description = (
            'The resource that is being accessed is locked.'
        )


    class _UnavailableForLegalReasons(exc.HTTPException):

        """*451* `Unavailable For Legal Reasons`

        This status code indicates that the server is denying access to the
        resource as a consequence of a legal demand.
        """
        code = 451
        description = (
            'Unavailable for legal reasons.'
        )

    # 400s
    HTTPBadRequest = exc.BadRequest
    HTTPUnauthorized = exc.Unauthorized
    HTTPForbidden = exc.Forbidden
    HTTPNotFound = exc.NotFound
    HTTPMethodNotAllowed = exc.MethodNotAllowed
    HTTPNotAcceptable = exc.NotAcceptable
    HTTPRequestTimeout = exc.RequestTimeout
    HTTPConflict = exc.Conflict
    HTTPGone = exc.Gone
    HTTPLengthRequired = exc.LengthRequired
    HTTPPreconditionFailed = exc.PreconditionFailed
    HTTPRequestEntityTooLarge = exc.RequestEntityTooLarge
    HTTPRequestURITooLarge = exc.RequestURITooLarge
    HTTPUnsupportedMediaType = exc.UnsupportedMediaType
    HTTPRequestedRangeNotSatisfiable = exc.RequestedRangeNotSatisfiable
    HTTPExpectationFailed = exc.ExpectationFailed
    HTTPImATeapot = exc.ImATeapot
    HTTPUnprocessableEntity = exc.UnprocessableEntity
    HTTPLocked = getattr(exc, 'Locked') if hasattr(exc, 'Locked') else _Locked
    HTTPPreconditionRequired = exc.PreconditionRequired
    HTTPTooManyRequests = exc.TooManyRequests
    HTTPRequestHeaderFieldsTooLarge = exc.RequestHeaderFieldsTooLarge
    HTTPUnavailableForLegalReasons = getattr(exc, 'UnavailableForLegalReasons') if hasattr(exc, 'UnavailableForLegalReasons') else _UnavailableForLegalReasons

    # 500s
    HTTPInternalServerError = exc.InternalServerError
    HTTPNotImplemented = exc.NotImplemented
    HTTPBadGateway = exc.BadGateway
    HTTPServiceUnavailable = exc.ServiceUnavailable
    HTTPGatewayTimeout = exc.GatewayTimeout
    HTTPHTTPVersionNotSupported = exc.HTTPVersionNotSupported
except ImportError:
    pass
