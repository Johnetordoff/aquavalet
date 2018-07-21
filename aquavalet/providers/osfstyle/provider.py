import re
import json
import aiohttp

from aquavalet.core import provider
from aquavalet.core import exceptions, streams
from aquavalet.providers.osfstorage.metadata import BaseOsfStorageItemMetadata
from aquavalet.settings import OSF_TOKEN

class OsfProvider(provider.BaseProvider):
    NAME = 'OSF'
    PATH_PATTERN = r'\/(?P<internal_provider>(?:\w|\d)+)?\/(?P<resource>[a-zA-Z0-9]{5,})?(?P<path>\/.*)?'

    def __init__(self, auth):
       self.token = OSF_TOKEN

    @property
    def default_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    async def validate_item(self, path):
        match = re.match(self.PATH_PATTERN, path)
        if match:
            groupdict = match.groupdict()
        else:
            raise exceptions.InvalidPathError('malfoarmed path no internal provider')

        if not groupdict.get('internal_provider'):
            raise exceptions.InvalidPathError('malfoarmed path no internal provider')
        self.internal_provider = groupdict.get('internal_provider')

        if not groupdict.get('resource'):
            raise exceptions.InvalidPathError('malfoarmed path no resource')
        self.resource = groupdict.get('resource')

        if not groupdict.get('path'):
            raise exceptions.InvalidPathError('malfoarmed path no path')
        elif groupdict.get('path') == '/':
            return BaseOsfStorageItemMetadata.root(self.internal_provider, self.resource)
        path = groupdict.get('path')

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f'https://api.osf.io/v2/files{path}/?meta=',
                headers=self.default_headers
            ) as resp:
                if resp.status == 200:
                    data = (await resp.json())['data']
                else:
                    raise self.handle_response(resp)

        return BaseOsfStorageItemMetadata(data['attributes'], path, self.internal_provider, self.resource)

    def can_duplicate_names(self):
        return True

    def can_intra_copy(self, other, path=None):
        return isinstance(other, self.__class__)

    def can_intra_move(self, other, path=None):
        return isinstance(other, self.__class__)

    async def intra_move(self, dest_provider, src_path, dest_path):
        pass

    async def intra_copy(self, dest_provider, src_path, dest_path):
        pass

    async def download(self, session, version=None, range=None, item=None):
        item = item or self.item

        resp = await session.get(
            url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
            headers=self.default_headers
        )
        return streams.ResponseStreamReader(resp)


    async def upload(self, stream, new_name):
        async def stream_sender(stream=None):
            chunk = await stream.read(64 * 1024)
            while chunk:
                yield chunk
                chunk = await stream.read(64 * 1024)

        async with aiohttp.ClientSession() as session:
            async with session.put(
                data=stream_sender(stream),
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{self.item.id}',
                headers=self.default_headers,
                params={'kind': 'file', 'name': new_name}
            ) as resp:
                print(resp)

    async def delete(self, confirm_delete=0, **kwargs):
        async with aiohttp.ClientSession() as session:
            async with await session.delete(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{self.item.id}',
                params={'confirm_delete': 0},
                headers=self.default_headers
            ) as resp:
                return resp


    async def metadata(self, version=None):
        return self.item

    async def create_folder(self, new_name):
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{self.item.id}',
                headers=self.default_headers,
                params={'kind': 'folder', 'name': new_name}
            ) as resp:
                return resp


    async def rename(self, new_name):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{self.item.id}',
                data=json.dumps({'action': 'rename', 'rename': new_name}),
                headers=self.default_headers
            ) as resp:
                print(resp)
                await resp.json()
                return resp

    async def children(self, item=None):
        item = item or self.item

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                headers=self.default_headers
            ) as resp:
                if resp.status == 200:
                    data = (await resp.json())['data']
                else:
                    raise self.handle_response(resp)

        return [BaseOsfStorageItemMetadata(metadata['attributes'], item.path, internal_provider=self.internal_provider, resource=self.resource) for metadata in data]

    async def parent(self):
        metadata = await self.root()

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{self.item.id}',
                headers=self.default_headers
            ) as resp:
                if resp.status == 200:
                    data = (await resp.json())['data']
                else:
                    raise self.handle_response(resp)

        return [BaseOsfStorageItemMetadata(metadata['attributes'], self.item.path, internal_provider=self.internal_provider, resource=self.resource) for metadata in data]

    async def root(self):
        return await self.validate_item('/')