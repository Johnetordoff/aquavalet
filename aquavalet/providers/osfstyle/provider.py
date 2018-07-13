import re
import json
import aiohttp

from aquavalet.core import provider
from aquavalet.core import exceptions, streams
from aquavalet.providers.osfstorage.metadata import BaseOsfStorageItemMetadata

class OsfProvider(provider.BaseProvider):
    NAME = 'OSF'
    PATH_PATTERN = r'\/(?P<internal_provider>(?:\w|\d)+)?\/(?P<resource>[a-zA-Z0-9]{5,})?(?P<path>\/.*)?'

    def __init__(self, auth, credentials, settings):
        super().__init__(auth, credentials, settings)
        self.token = credentials["token"]

    @property
    def default_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    async def validate_path(self, path):
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
        self.path = groupdict.get('path')

        resp = await self.make_request(
            method='GET',
            url=f'https://api.osf.io/v2/files{self.path}/?meta=',
            throws=exceptions.ProviderError,
            expects=(200,)
        )

        data = (await resp.json())['data']
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

    async def download(self, session, path, version=None, range=None):
        resp = await session.get(
            url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{path.id}',
            headers=self.default_headers
        )
        return streams.ResponseStreamReader(resp)


    async def upload(self, stream, path, new_name):
        async def stream_sender(stream=None):
            chunk = await stream.read(64 * 1024)
            while chunk:
                yield chunk
                chunk = await stream.read(64 * 1024)

        async with aiohttp.ClientSession() as session:
            async with await session.put(
                data=stream_sender(stream),
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{path.id}',
                headers=self.default_headers,
                params={'kind': 'file', 'name': new_name}
            ) as resp:
                print(resp)

    async def delete(self, path, confirm_delete=0, **kwargs):
        await self.make_request(
            method='DELETE',
            url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{path.id}?meta=',
            throws=exceptions.ProviderError,
            expects=(204,)
        )

    async def metadata(self, path, **kwargs):
        return path

    async def create_folder(self, path, **kwargs):
        pass

    async def rename(self, path, new_name):
        resp = await self.make_request(
            method='POST',
            url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{path.id}',
            throws=exceptions.ProviderError,
            data=json.dumps({'action': 'rename', 'rename': new_name}),
            expects=(200,)
        )
        print(resp)
        print(await resp.json())
        return resp

    async def children(self, path):
        resp = await self.make_request(
            method='GET',
            url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{path.id}?meta=',
            throws=exceptions.ProviderError,
            expects=(200,)
        )
        data = (await resp.json())['data']

        return [BaseOsfStorageItemMetadata(metadata['attributes'], path.path, internal_provider=self.internal_provider, resource=self.resource) for metadata in data]
