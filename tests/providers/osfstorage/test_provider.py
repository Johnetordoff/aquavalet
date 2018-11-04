import pytest
import aiohttp

from aquavalet.providers.osfstorage.metadata import OsfMetadata
from aquavalet.streams.http import ResponseStreamReader
from aquavalet.exceptions import (
    InvalidPathError,
    NotFoundError
)


class TestValidateItem:

    @pytest.mark.asyncio
    async def test_validate_item_no_internal_provider(self, provider, file_metadata_resp, aresponses):
        aresponses.add('api.osf.io', '/v2/files/5b6ee0c390a7e0001986aff5/', 'get', file_metadata_resp)

        with pytest.raises(InvalidPathError) as exc:
            await provider.validate_item('/badpath')

        assert exc.value.message == 'No internal provider in url, path must follow pattern {}'.format(provider.PATH_PATTERN)

        with pytest.raises(InvalidPathError) as exc:
            await provider.validate_item('/badpath/')

        assert exc.value.message == 'No resource in url, path must follow pattern {}'.format(provider.PATH_PATTERN)

        with pytest.raises(InvalidPathError):
            await provider.validate_item('/badpath/das')

        assert exc.value.message == 'No resource in url, path must follow pattern {}'.format(provider.PATH_PATTERN)

        with pytest.raises(InvalidPathError):
            await provider.validate_item('/badpath/guid0')

        assert exc.value.message == 'No resource in url, path must follow pattern {}'.format(provider.PATH_PATTERN)

    @pytest.mark.asyncio
    async def test_validate_item_404(self, provider, response_404, aresponses):
        aresponses.add('api.osf.io', '/v2/files/not-root/', 'get', response_404)

        with pytest.raises(NotFoundError) as exc:
            await provider.validate_item('/osfstorage/guid0/not-root')

        assert exc.value.message == 'Item at path \'/not-root\' cannot be found.'

    @pytest.mark.asyncio
    async def test_validate_item_root(self, provider, folder_metadata_resp, aresponses):
        aresponses.add('api.osf.io', '/v2/files/5b6ee0c390a7e0001986aff5/', 'get', folder_metadata_resp)
        item = await provider.validate_item('/osfstorage/guid0/')

        assert isinstance(item, OsfMetadata)

        assert item.id == '/'
        assert item.path == '/'
        assert item.name == 'osfstorage root'
        assert item.kind == 'folder'
        assert item.mimetype is None

    @pytest.mark.asyncio
    async def test_validate_item(self, provider, folder_metadata_resp, aresponses):
        aresponses.add('api.osf.io', '/v2/files/5b6ee0c390a7e0001986aff5/', 'get', folder_metadata_resp)
        item = await provider.validate_item('/osfstorage/guid0/5b6ee0c390a7e0001986aff5' )

        assert isinstance(item, OsfMetadata)

        assert item.id == '/5b5de758f63e210010ec8f53/'
        assert item.path == '/5b5de758f63e210010ec8f53/'
        assert item.name == 'test_folder'
        assert item.kind == 'folder'
        assert item.mimetype is None


class TestDownload:

    @pytest.mark.asyncio
    async def test_download(self, provider, file_metadata_object, download_resp, aresponses):
        aresponses.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage' + file_metadata_object.id, 'get', download_resp)

        async with aiohttp.ClientSession() as session:
            stream = await provider.download(file_metadata_object, session)

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name == None
        assert stream.content_type == 'application/octet-stream'
        assert await stream.read() == b'test stream!'

    @pytest.mark.asyncio
    async def test_download_range(self, provider, file_metadata_object, download_resp, aresponses):
        aresponses.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage' + file_metadata_object.id, 'get', download_resp)

        async with aiohttp.ClientSession() as session:
            stream = await provider.download(file_metadata_object, session, range=(0,3))

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name == None
        assert stream.content_type == 'application/octet-stream'
        assert await stream.read() == b'test stream!'  # this should really be truncated, but it's done by osf which is mocked.


class TestUpload:

    @pytest.mark.asyncio
    async def test_upload(self, provider, file_metadata_object, upload_resp, aresponses, request_stream):
        aresponses.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage' + file_metadata_object.id, 'put', upload_resp)

        item = await provider.upload(item=file_metadata_object, stream=request_stream, new_name='test.txt', conflict='warn')

        assert isinstance(item, OsfMetadata)
        assert item.name == 'test.txt'
        assert item.mimetype == 'text/plain'


class TestDelete:

    @pytest.mark.asyncio
    async def test_delete(self, provider, file_metadata_object, delete_resp, aresponses):
        aresponses.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage' + file_metadata_object.id, 'delete', delete_resp)

        item = await provider.delete(file_metadata_object)

        assert item is None


class TestCreateFolder:

    @pytest.mark.asyncio
    async def test_create_folder(self, provider, file_metadata_object, create_folder_resp, aresponses):
        aresponses.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage' + file_metadata_object.id, 'put', create_folder_resp)

        item = await provider.create_folder(file_metadata_object, 'test')

        assert isinstance(item, OsfMetadata)
        assert item.name == 'test'
        assert item.mimetype is None


class TestRename:

    @pytest.mark.asyncio
    async def test_rename(self, provider, file_metadata_object, file_metadata_resp, aresponses):
        aresponses.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage' + file_metadata_object.id, 'post', file_metadata_resp)
        item = await provider.rename(file_metadata_object, 'new_name')

        assert isinstance(item, OsfMetadata)
        assert item.path == '/5b6ee0c390a7e0001986aff5'
        assert item.kind == 'file'
        assert item.name == 'test.txt'  # this should really be 'new_name, but it's done by osf which is mocked.


class TestChildren:

    @pytest.mark.asyncio
    async def test_children(self, provider, file_metadata_object, children_resp, aresponses):
        aresponses.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage' + file_metadata_object.id, 'get', children_resp)
        item = await provider.children(file_metadata_object)

        assert isinstance(item, list)
        assert len(item) == 2
        assert item[0].path == '/5b537030c86a8c001243ce7a'
        assert item[0].name == 'test-1'
        assert item[0].kind == 'file'
        assert item[1].path == '/5b4247025b38c4001068a7b6/'
        assert item[1].name == 'test2'
        assert item[1].kind == 'folder'

