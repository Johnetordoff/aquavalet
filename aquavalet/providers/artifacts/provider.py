import re
from aquavalet.core import exceptions

from aquavalet.providers.osfstyle.provider import OsfProvider
from aquavalet.providers.artifacts.metadata import ArtifactsMetadata
from aquavalet.settings import ARTIFACTS_TOKEN
import aiohttp


class ArtifactsProvider(OsfProvider):
    NAME = 'artifacts'
    BASE_URL = 'https://files.artifacts.ai/v1/resources/'
    API_URL = 'https://api.artifacts.ai/v2/files{}/?meta='

    Item = ArtifactsMetadata


    def __init__(self, auth):
       self.token = ARTIFACTS_TOKEN


    async def upload(self, stream, new_name, item=None):
        item = item or self.item

        headers = {'Content-Length': str(stream.size)}
        headers.update(self.default_headers)

        async with aiohttp.ClientSession() as session:
            async with session.put(
                data=stream.generator.stream_sender(),
                url=self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{item.id}',
                headers=headers,
                params={'kind': 'file', 'name': new_name}
            ) as resp:
                print(resp)
                print(await resp.json())


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
                    url=f'https://api.artifacts.ai/v2/nodes/{self.resource}/files/{self.internal_provider}{path}',
                    headers=self.default_headers
                ) as resp:
                    if resp.status == 200:
                        data = (await resp.json())['data']
                        if type(data) == list:
                            return await self.parent(item=self.Item(data[0]['attributes'], path, self.internal_provider, self.resource))
                        else:
                            return self.Item(data['attributes'], path, self.internal_provider, self.resource)
                    else:
                        raise await self.handle_response(resp, path=path)
