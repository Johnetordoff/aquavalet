import json
from aiohttp import web
import logging


from aquavalet.server.routes import routes

logger = logging.getLogger(__name__)


def json_error(status_code: int, exception: Exception) -> web.Response:
    """
    Returns a Response from an exception.
    Used for error middleware.
    :param status_code:
    :param exception:
    :return:
    """

    json_body = json.dumps(
        {"error": exception.__class__.__name__, "message": exception.message}
    )

    return web.json_response(status=status_code, body=json_body)


async def error_middleware(app: web.Application, handler):
    """
    This middleware handles with exceptions received from views or previous middleware.
    :param app:
    :param handler:
    :return:
    """

    async def middleware_handler(request):
        try:
            return await handler(request)
        except web.HTTPException as ex:
            return json_error(ex.status, ex)
        except Exception as e:
            logger.warning(
                "Request {} has failed with exception: {}".format(request, repr(e))
            )
            return json_error(500, e)

    return middleware_handler


def app():
    app = web.Application(middlewares=[error_middleware])
    app.add_routes(routes)
    return app
