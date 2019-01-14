import asyncio
from aiohttp import web
import logging

from tornado.platform.asyncio import AsyncIOMainLoop

from aquavalet.server.request_handler import ProviderHandler
from aquavalet.server.handlers import routes
from aquavalet import settings

logger = logging.getLogger(__name__)


def app():
    app = web.Application()
    #app.add_routes([web.get('/', handlers.RootHandler)])
    app.add_routes(routes)
     #   [ProviderHandler.as_entry()]
     #   [(r'/', handlers.RootHandler),
     #   (r'/status/', handlers.StatusHandler)],
     #   debug=debug,
    #)
    return app