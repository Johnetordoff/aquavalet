from aquavalet.core import provider
from aquavalet.core import exceptions, streams
from aquavalet.core.path import WaterButlerPath
from aquavalet.providers.filesystem.metadata import FileSystemItemMetadata

class OsfProvider(provider.BaseProvider):
    NAME = 'OSF'

    def __init__(self, auth, credentials, settings):
        super().__init__(auth, credentials, settings)
        self.token = credentials["token"]
        self.BASE_URL = settings['base_url']

    @property
    def default_headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    async def validate_path(self, path):
        segment_list = [segment for segment in path.split('/') if segment != '']
        if not segment_list:
            raise exceptions.InvalidPathError('malfoarmed path no provider')

        try:
            self.provider = segment_list[0]
        except IndexError:
            raise exceptions.InvalidPathError('malfoarmed path no provider')

        try:
            self.resource = segment_list[1]
        except IndexError:
            raise exceptions.InvalidPathError('malfoarmed path no resource')

        ids = ['']
        metadata = {'path': '/', 'kind': 'folder'}

        for segment in segment_list[2:]:

            resp = await self.make_request(
                method='GET',
                url=self.BASE_URL + f'{self.resource}/providers/{self.provider}{metadata["path"]}'
            )

            resp_metadata = (await resp.json())['data']
            parts = [part_metadata['attributes'] for part_metadata in resp_metadata if part_metadata['attributes']['name'].lstrip('/').rstrip('/') == segment]
            if parts:
                metadata = parts[0]
                ids.append(metadata['path'])

        file_path = '/' + '/'.join(segment_list[2:]) if len(segment_list) > 2 else '/'
        return WaterButlerPath(file_path, _ids=ids, folder=metadata['kind'] == 'folder')

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

    async def download(self, path, version=None, range=None):
        resp = await self.make_request(
            method='GET',
            url=self.BASE_URL + f'{self.resource}/providers/{self.provider}/{path.identifier}'
        )
        return streams.ResponseStreamReader(resp)

    async def upload(self, stream, path):
        resp = await self.make_request(
            method='PUT',
            url=self.BASE_URL + f'{self.resource}/providers/{self.provider}/{path.path}',
            params={'name': path.identifier, 'kind': 'file'},
            data=stream
        )
        metadata = await resp.json()
        return FileSystemItemMetadata(metadata['data'], self.resource, path)

    async def delete(self, path, confirm_delete=0, **kwargs):
        pass

    async def metadata(self, path, **kwargs):
        resp = await self.make_request(
            method='GET',
            url=self.BASE_URL + f'{self.resource}/providers/{self.provider}/{path.parent.identifier}'
        )
        metadata = [metadata['attributes'] for metadata in (await resp.json())['data'] if metadata['attributes']['materialized'].lstrip('/').rstrip('/') == path.path.lstrip('/').rstrip('/')][0]
        return FileSystemItemMetadata(metadata, self.resource, path)

    async def create_folder(self, path, **kwargs):
        pass

    async def _item_metadata(self, path, revision=None):
        pass

    async def children(self, path):
        resp = await self.make_request(
            method='GET',
            url=self.BASE_URL + f'{self.resource}/providers/{self.provider}/{path.identifier}',
            throws=exceptions.ProviderError,
            expects=(200,)
        )
        if resp.headers['CONTENT-TYPE'] == 'application/json; charset=UTF-8':
            return [FileSystemItemMetadata(metadata['attributes'], self.resource, path) for metadata in (await resp.json())['data']]
        else:
            raise exceptions.MetadataError(code=400, message='File is has no children')
