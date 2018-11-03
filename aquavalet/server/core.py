import tornado.web
import tornado.gen
import tornado.iostream

from aquavalet import settings
from aquavalet.core import exceptions


CORS_ACCEPT_HEADERS = [
    'Range',
    'Content-Type',
    'Authorization',
    'Cache-Control',
    'X-Requested-With',
]

CORS_EXPOSE_HEADERS = [
    'Range',
    'Accept-Ranges',
    'Content-Range',
    'Content-Length',
    'Content-Encoding',
]

class BaseHandler(tornado.web.RequestHandler):

    @classmethod
    def as_entry(cls):
        return (cls.PATTERN, cls)

    def write_error(self, status_code, exc_info):
        etype, exc, _ = exc_info

        if issubclass(etype, exceptions.WaterButlerError):
            self.set_status(int(exc.code))
            exception_kwargs = {'data': {'level': 'info'}} if exc.is_user_error else {}
            finish_args = [exc.data] if exc.data else [{'code': exc.code, 'message': exc.message}]
        else:
            finish_args = [{'code': status_code, 'message': self._reason}]

        self.finish(*finish_args)

    def set_status(self, code, reason=None):
        return super().set_status(code, reason)

    def _cross_origin_is_allowed(self):
        if self.request.method == 'OPTIONS':
            return True
        elif not self.request.cookies and self.request.headers.get('Authorization'):
            return True
        return False

    def set_default_headers(self):
        if not self.request.headers.get('Origin'):
            return

        allowed_origin = None
        if self._cross_origin_is_allowed():
            allowed_origin = self.request.headers['Origin']
        elif isinstance(settings.CORS_ALLOW_ORIGIN, str):
            if settings.CORS_ALLOW_ORIGIN == '*':
                # Wild cards cannot be used with allowCredentials.
                # Match Origin if its specified, makes pdfs and pdbs render properly
                allowed_origin = self.request.headers['Origin']
            else:
                allowed_origin = settings.CORS_ALLOW_ORIGIN
        else:
            if self.request.headers['Origin'] in settings.CORS_ALLOW_ORIGIN:
                allowed_origin = self.request.headers['Origin']

        if allowed_origin is not None:
            self.set_header('Access-Control-Allow-Origin', allowed_origin)

        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Access-Control-Allow-Headers', ', '.join(CORS_ACCEPT_HEADERS))
        self.set_header('Access-Control-Expose-Headers', ', '.join(CORS_EXPOSE_HEADERS))
        self.set_header('Cache-control', 'no-store, no-cache, must-revalidate, max-age=0')


def parse_request_range(range_header):
    request_range = tornado.httputil._parse_request_range(range_header)

    if request_range is None:
        return request_range

    start, end = request_range
    if start is None or start < 0:
        return None

    if end is not None:
        end -= 1
        if end < start:
            return None

    return start, end
