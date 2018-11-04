import json
from http import HTTPStatus


DEFAULT_ERROR_MSG = 'An error occurred while making a {response.method} request to {response.url}'


class WaterButlerError(Exception):
    """The base exception that all others are subclasses of. Provides ``__str__`` and ``__repr__``.

    Exceptions in WaterButler need to be able to survive a pickling/unpickling process.  Because of
    a quirk in the implementation of exceptions, an unpickled exception will have its ``__init__``
    method called with the same positional arguments that ``Exception.__init__()`` is called with.
    Since WaterButlerError calls ``Exception.__init__()`` with the integer status code, all of its
    children must handle being initialized with a single integer positional argument.  IOW,
    ``ChildOfWaterButlerError.__init__(999)`` must always succeed, even if the result error message
    is nonsense.  After calling ``__init__``, the unpickling process will update the exception's
    internal ``__dict__`` to the same state as before pickling, so the exception will end up being
    accurate/meaningful/sensible.

    **In summary:**

    * No child of WaterButlerError can have a signature with anything other than one positional
      argument.

    * It must not perform any methods on the positional arg that are not compatible with integers.

    * kwargs are not passed as part of the faux __init__ call, so a class must be able to be
      instantiated with defaults only.

    * It is not necessary that the exception be meaningful when called this way.  It will be made
      consistent after initialization.

    """

    def __init__(self, message,log_message=None,
                 is_user_error=False):
        self.log_message = log_message
        self.is_user_error = is_user_error
        if isinstance(message, dict):
            self.data = message
            self.message = json.dumps(message)
        else:
            self.data = None
            self.message = message

    def __repr__(self):
        return '<{}({}, {})>'.format(self.__class__.__name__, self.code, self.message)

    def __str__(self):
        return '{}, {}'.format(self.code, self.message)


class InvalidParameters(WaterButlerError):
    """Errors regarding incorrect data being sent to a method should raise either this
    Exception or a subclass thereof.  Defaults status code to 400, Bad Request.
    """
    code = 400

class UnsupportedHTTPMethodError(WaterButlerError):
    """An unsupported HTTP method was used.
    """
    def __init__(self, method, supported=None):

        if supported is None:
            supported_methods = 'unspecified'
        else:
            supported_methods = ', '.join(list(supported)).upper()

        super().__init__('Method "{}" not supported, currently supported methods '
                         'are {}'.format(method, supported_methods),
                         code=HTTPStatus.METHOD_NOT_ALLOWED, is_user_error=True)


class PluginError(WaterButlerError):
    """WaterButler-related errors raised from a plugin, such as an auth handler or provider, should
    inherit from `PluginError`.
    """
    pass

class InvalidPathError(PluginError):
    code = 400

class AuthError(PluginError):
    code = 401

class Forbidden(PluginError):
    code = 403

class NotFoundError(PluginError):
    code = 404

class Conflict(PluginError):
    code = 409

class Gone(PluginError):
    code = 410

class ProviderError(PluginError):
    """WaterButler-related errors raised from :class:`aquavalet.core.provider.BaseProvider`
    should inherit from ProviderError.
    """
    pass


class UnhandledProviderError(ProviderError):
    """Errors inheriting from UnhandledProviderError represent unanticipated status codes received
    from the provider's API.  These are the only ones that should be passed to the ``throws``
    argument of `make_request`.  All have the same signature, ``(message, code: int=500)`` and are
    instantiated by the `exception_from_response` method at the end of this module.

    Developer-defined errors should **not** inherit from `UnhandledProviderError`.
    """
    pass


class CopyError(UnhandledProviderError):
    pass


class CreateFolderError(UnhandledProviderError):
    pass


class DeleteError(UnhandledProviderError):
    pass


class DownloadError(UnhandledProviderError):
    pass


class IntraCopyError(UnhandledProviderError):
    pass


class IntraMoveError(UnhandledProviderError):
    pass


class MoveError(UnhandledProviderError):
    pass


class MetadataError(UnhandledProviderError):
    pass


class RevisionsError(UnhandledProviderError):
    pass


class UploadError(UnhandledProviderError):
    pass

