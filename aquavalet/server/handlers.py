from aiohttp import web
from aquavalet import settings

routes = web.RouteTableDef()

@routes.get('/status')
async def get_handler(request):
    return web.json_response({'status': 'up'})

@routes.get('/')
async def index(request):
    return web.Response(text='Hi')
