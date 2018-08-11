import re
import json
import aiohttp

from aquavalet.core import provider
from aquavalet.core import exceptions, streams

class OsfProvider(provider.BaseProvider):
    NAME = 'OSF'
    PATH_PATTERN = r'\/(?P<internal_provider>(?:\w|\d)+)?\/(?P<resource>[a-zA-Z0-9]{5,})?(?P<path>\/.*)?'

    @property
    def default_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    async def validate_item(self, path):
        match = re.match(self.PATH_PATTERN, path)
        if match:
            groupdict = match.groupdict()
        else:
            raise exceptions.InvalidPathError(f'No internal provider in url, path must follow pattern {self.PATH_PATTERN}')

        if not groupdict.get('internal_provider'):
            raise exceptions.InvalidPathError(f'No internal provider in url, path must follow pattern {self.PATH_PATTERN}')
        self.internal_provider = groupdict.get('internal_provider')

        if not groupdict.get('resource'):
            raise exceptions.InvalidPathError(f'No resource in url, path must follow pattern {self.PATH_PATTERN}')
        self.resource = groupdict.get('resource')

        if not groupdict.get('path'):
            raise exceptions.InvalidPathError(f'No path in url, path must follow pattern {self.PATH_PATTERN}')
        elif groupdict.get('path') == '/':
            return self.Item.root(self.internal_provider, self.resource)
        path = groupdict.get('path')

        if self.internal_provider == 'osfstorage':
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=self.API_URL.format(path=path),
                    headers=self.default_headers
                ) as resp:
                    if resp.status == 200:
                        data = (await resp.json())['data']
                    else:
                        raise await self.handle_response(resp, path=path)

        return self.Item(data['attributes'], self.internal_provider, self.resource)

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

    async def upload(self, stream, new_name, item=None):
        item = item or self.item

        async with aiohttp.ClientSession() as session:
            async with session.put(
                data=stream.generator.stream_sender(),
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                headers=self.default_headers,
                params={'kind': 'file', 'name': new_name}
            ) as resp:
                print(resp)
                print(await resp.json())

    async def delete(self, confirm_delete=0, item=None):
        item = item or self.item

        async with aiohttp.ClientSession() as session:
            async with await session.delete(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                params={'confirm_delete': 0},
                headers=self.default_headers
            ) as resp:
                print(resp)


    async def metadata(self, version=None):
        return self.item

    async def create_folder(self, new_name, item=None):
        item = item or self.item

        async with aiohttp.ClientSession() as session:
            async with session.put(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                headers=self.default_headers,
                params={'kind': 'folder', 'name': new_name}
            ) as resp:
                if resp.status in (200, 201):
                    data = (await resp.json())['data']
                else:
                    raise await self.handle_response(resp, item)

                return self.Item(data['attributes'], item, self.internal_provider, self.resource)

    async def rename(self, new_name, item=None):
        item = item or self.item

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                data=json.dumps({'action': 'rename', 'rename': new_name}),
                headers=self.default_headers
            ) as resp:
                print(resp)

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
                    raise await self.handle_response(resp, item)

        return [self.Item(metadata['attributes'], item.path, internal_provider=self.internal_provider, resource=self.resource) for metadata in data]

    async def parent(self, item=None):
        item = item or self.item

        if item.is_root:
            return item

        if item.unix_path_parent == '/':
            return await self.root(item=item)

        name = ''
        child_link = self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}/'
        while name != item.unix_path_parent:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=child_link + '?meta=',
                    headers=self.default_headers
                ) as resp:
                    if resp.status == 200:
                        data = (await resp.json())['data']
                        for child_item in data:
                            unix_path = child_item['attributes']['materialized']
                            if unix_path in item.unix_path_parent:
                                child_link = child_item['links']['move']
                                name = child_item['attributes']['materialized']
                    else:
                        raise await self.handle_response(resp, item)

        return self.Item(child_item['attributes'], item.path, internal_provider=self.internal_provider, resource=self.resource)

    async def root(self, item=None):
        if item.is_root:
            return self

        return await self.validate_item(f'/{self.internal_provider}/{self.resource}/')