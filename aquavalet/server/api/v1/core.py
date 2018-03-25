import tornado.web
import tornado.gen
import tornado.iostream

from aquavalet import tasks
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

        exception_kwargs, finish_args = {}, []
        if issubclass(etype, exceptions.WaterButlerError):
            self.set_status(int(exc.code))
            exception_kwargs = {'data': {'level': 'info'}} if exc.is_user_error else {}
            finish_args = [exc.data] if exc.data else [{'code': exc.code, 'message': exc.message}]
        elif issubclass(etype, tasks.WaitTimeOutError):
            self.set_status(202)
            exception_kwargs = {'data': {'level': 'info'}}
        else:
            finish_args = [{'code': status_code, 'message': self._reason}]

        self.finish(*finish_args)

    # avoid dumping duplicate information to application log
    def log_exception(self, typ, value, tb):
        if isinstance(value, tornado.web.HTTPError):
            if value.log_message:
                format = "%d %s: " + value.log_message
                args = ([value.status_code, self._request_summary()] +
                        list(value.args))
                tornado.web.gen_log.warning(format, *args)
        else:
            tornado.web.app_log.error("Uncaught exception %s\n", self._request_summary(),
                                      exc_info=(typ, value, tb))


    def set_status(self, code, reason=None):
        return super().set_status(code, reason)

    async def write_stream(self, stream):
        try:
            while True:
                chunk = await stream.read(settings.CHUNK_SIZE)
                if not chunk:
                    break
                if isinstance(chunk, bytearray):
                    chunk = bytes(chunk)
                self.write(chunk)
                self.bytes_downloaded += len(chunk)
                del chunk
                await self.flush()
        except tornado.iostream.StreamClosedError:
            # Client has disconnected early.
            # No need for any exception to be raised
            return

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

    def options(self, *args, **kwargs):
        self.set_status(204)
        if self.request.headers.get('Origin'):
            self.set_header('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE'),



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
