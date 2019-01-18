from aiohttp import web
from aiohttp import hdrs
from aquavalet import settings
from aquavalet import utils

routes = web.RouteTableDef()

@routes.get('/status')
async def get_handler(request):
    return web.json_response({'status': 'up'})


@routes.view(r'/{provider:(?:osfstorage|filesystem)+}{path:/.*/?}')
class MyView(web.View):

    bytes_downloaded = 0
    bytes_uploaded = 0

    SUPPORTED_METHODS = hdrs.METH_ALL.union({'METADATA',
                         'CHILDREN',
                         'UPLOAD',
                         'CREATE_FOLDER',
                         'RENAME',
                         'DOWNLOAD',
                         'VERSIONS',
                         'MOVE',
                         'COPY'})

    async def _iter(self):
        if self.request.method not in self.SUPPORTED_METHODS:
            self._raise_allowed_methods()
        method = getattr(self, self.request.method.lower(), None)
        if method is None:
            self._raise_allowed_methods()
        await self.prepare()
        resp = await method()
        return resp

    async def prepare(self):
        request = self.request

        provider = request.match_info['provider']
        path = request.match_info.get('path')

        auth = None  # Figure out best approach
        self.provider = utils.make_provider(provider, auth)
        self.provider.item = await self.provider.validate_item(path)

    #async def get(self):
    #    return web.json_response(self.request.match_info)

    async def get(self):

        version = self.request.query.get('version')
        metadata = await self.provider.metadata(self.provider.item, version=version)

        return web.json_response({'data': metadata.json_api_serialized()})

    async def post(self):
        pass