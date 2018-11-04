import json
from http import HTTPStatus


DEFAULT_ERROR_MSG = 'An error occurred while making a {response.method} request to {response.url}'


class WaterButlerError(Exception):

    def __init__(self, message):
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

    def __init__(self, filename):
        self.message =  f'Item at \'{filename}\' could not be found, folders must end with \'/\''
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

