import asyncio
import logging

import tornado.web
from tornado.platform.asyncio import AsyncIOMainLoop

from aquavalet.server.request_handler import ProviderHandler
from aquavalet.server import handlers
from aquavalet import settings

logger = logging.getLogger(__name__)


def make_app(debug):
    app = tornado.web.Application(
        [ProviderHandler.as_entry()] +
        [(r'/', handlers.RootHandler),
        (r'/status/', handlers.StatusHandler)],
        debug=debug,
    )
    return app


def serve():
    AsyncIOMainLoop().install()

    app = make_app(settings.DEBUG)

    app.listen(settings.PORT, address=settings.ADDRESS)

    logger.info("Listening on {0}:{1}".format(settings.ADDRESS, settings.PORT))

    asyncio.get_event_loop().set_debug(settings.DEBUG)
    asyncio.get_event_loop().run_forever()
