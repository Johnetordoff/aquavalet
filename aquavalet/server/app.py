import os
import signal
import asyncio
import logging
from functools import partial

import tornado.web
import tornado.platform.asyncio

from aquavalet.server.request_handler import ProviderHandler
from aquavalet.server.api import v1
from aquavalet.server import handlers
from aquavalet.server import settings as server_settings

logger = logging.getLogger(__name__)

HANDLERS = [
    ProviderHandler.as_entry()
]


def sig_handler(sig, frame):
    io_loop = tornado.ioloop.IOLoop.instance()

    def stop_loop():
        if len(asyncio.Task.all_tasks(io_loop)) == 0:
            io_loop.stop()
        else:
            io_loop.call_later(1, stop_loop)

    io_loop.add_callback_from_signal(stop_loop)


def api_to_handlers(api):
    return [
        (os.path.join('/', pattern.lstrip('/')), handler)
        for (pattern, handler) in HANDLERS
    ]


def make_app(debug):
    app = tornado.web.Application(
        api_to_handlers(v1) +
        [(r'/', handlers.RootHandler)],
        [(r'/status', handlers.StatusHandler)],
        debug=debug,
    )
    return app


def serve():
    tornado.platform.asyncio.AsyncIOMainLoop().install()

    app = make_app(server_settings.DEBUG)

    ssl_options = None
    if server_settings.SSL_CERT_FILE and server_settings.SSL_KEY_FILE:
        ssl_options = {
            'certfile': server_settings.SSL_CERT_FILE,
            'keyfile': server_settings.SSL_KEY_FILE,
        }

    app.listen(
        server_settings.PORT,
        address=server_settings.ADDRESS,
        xheaders=server_settings.XHEADERS,
        max_body_size=server_settings.MAX_BODY_SIZE,
        ssl_options=ssl_options,
    )

    logger.info("Listening on {0}:{1}".format(server_settings.ADDRESS, server_settings.PORT))

    signal.signal(signal.SIGTERM, partial(sig_handler))
    asyncio.get_event_loop().set_debug(server_settings.DEBUG)
    asyncio.get_event_loop().run_forever()
