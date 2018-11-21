import tornado.web
import tornado.gen
import tornado.iostream

from aquavalet import settings, exceptions

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
        self.set_status(int(exc.code))
        finish_args = [{'code': exc.code, 'message': exc.message}]
        self.finish(*finish_args)

    def set_status(self, code, reason=None):
        return super().set_status(code, reason)

    def _cross_origin_is_allowed(self):
        if self.request.method == 'OPTIONS':
            return True
        elif not self.request.cookies and self.request.headers.get('Authorization'):
            return True
        return False

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
