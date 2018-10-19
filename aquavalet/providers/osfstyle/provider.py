import json
import aiohttp

from aquavalet.core import provider

from aquavalet.core import streams
from aquavalet.core import exceptions
from aquavalet.providers.utils import require_group, require_match

message_no_internal_provider = 'No internal provider in url, path must follow pattern ^\/(?P<internal_provider>(?:\w|\d)+)?\/(?P<resource>[a-zA-Z0-9]{5,})?(?P<path>\/.*)?'
message_no_resource = 'No internal provider in url, path must follow pattern ^\/(?P<internal_provider>(?:\w|\d)+)?\/(?P<resource>[a-zA-Z0-9]{5,})?(?P<path>\/.*)?'
message_no_path = 'No path in url, path must follow pattern ^\/(?P<internal_provider>(?:\w|\d)+)?\/(?P<resource>[a-zA-Z0-9]{5,})?(?P<path>\/.*)?'

class OsfProvider(provider.BaseProvider):
    NAME = 'OSF'
    PATH_PATTERN = r'^\/(?P<internal_provider>(?:\w|\d)+)?\/(?P<resource>[a-zA-Z0-9]{5,})?(?P<path>\/.*)?'

    @property
    def default_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    async def validate_item(self, path):
        match = require_match(self.PATH_PATTERN, path, 'match could not be found')

        self.internal_provider = require_group(match, 'internal_provider', message_no_internal_provider)
        self.resource = require_group(match, 'resource', message_no_resource)
        path = require_group(match, 'path', message_no_path)
        if path == '/':
            return self.Item.root(self.internal_provider, self.resource)

        if self.internal_provider == 'osfstorage':
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=self.API_URL.format(path=path),
                    headers=self.default_headers,
                ) as resp:
                    if resp.status == 200:
                        data = (await resp.json())['data']
                    else:
                        raise await self.handle_response(resp, path=path)

        return self.Item(data['attributes'], self.internal_provider, self.resource)

    async def download(self, item, session, version=None, range=None):
        download_header = self.default_headers

        if range:
            download_header.update({'Range': str(self._build_range_header(range))})

        resp = await session.get(
            url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
            headers=download_header
        )
        return streams.ResponseStreamReader(resp, range)

    async def upload(self, item, stream, new_name, conflict):

        async with aiohttp.ClientSession() as session:
            async with session.put(
                data=stream.generator.stream_sender(),
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                headers=self.default_headers,
                params={'kind': 'file', 'name': new_name, 'conflict': conflict}
            ) as resp:
                if resp.status in (200, 201):
                    data = (await resp.json())['data']
                else:
                    return await self.handle_response(resp=resp, item=item, new_name=new_name, stream=stream, conflict=conflict)

            return self.Item(data['attributes'], self.internal_provider, self.resource)

    async def handle_conflict_replace(self, resp, item, path, stream, new_name, conflict):
        children = await self.children(item)

        for item in children:
            if item.name == new_name:
                break

        async with aiohttp.ClientSession() as session:
            async with session.put(
                data=stream.generator.stream_sender(),
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                headers=self.default_headers,
            ) as resp:
                if resp.status in (200, 201):
                    data = (await resp.json())['data']
                else:
                    return await self.handle_response(resp=resp, item=item, new_name=new_name, stream=stream, conflict=conflict)

            return self.Item(data['attributes'], self.internal_provider, self.resource)

    async def delete(self, item, confirm_delete=0):
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                params={'confirm_delete': 0},
                headers=self.default_headers
            ) as resp:
                if resp.status in (204,):
                    return None
                else:
                    raise await self.handle_response(resp, item)


    async def metadata(self, item, version=None):
        return item

    async def create_folder(self, item, new_name):
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                headers=self.default_headers,
                params={'kind': 'folder', 'name': new_name}
            ) as resp:
                if resp.status in (201,):
                    data = (await resp.json())['data']
                else:
                    raise await self.handle_response(resp, item, new_name=new_name)

                return self.Item(data['attributes'], self.internal_provider, self.resource)

    async def rename(self, item, new_name):

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                data=json.dumps({'action': 'rename', 'rename': new_name}),
                headers=self.default_headers
            ) as resp:
                if resp.status == 200:
                    data = (await resp.json())['data']
                else:
                    raise await self.handle_response(resp, item)

                return self.Item(data['attributes'], self.internal_provider, self.resource)

    async def children(self, item):

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                headers=self.default_headers
            ) as resp:
                if resp.status == 200:
                    data = (await resp.json())['data']
                else:
                    raise await self.handle_response(resp, item)

        return [self.Item(metadata['attributes'], internal_provider=self.internal_provider, resource=self.resource) for metadata in data]
