import pytest
import aiohttp

from .fixtures import (
    provider,
    response_404,
    response_404_json,
    file_metadata_json,
    file_metadata_resp,
    folder_metadata_json,
    folder_metadata_resp,
    file_metadata_object,
    download_resp

)

from aquavalet.providers.osfstorage.metadata import OsfMetadata
from aquavalet.core.streams import ResponseStreamReader
from aquavalet.core.exceptions import (
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
            stream = await provider.download(session, item=file_metadata_object)

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name == None
        assert stream.content_type == 'application/octet-stream'
        assert await stream.read() == b'test stream!'

    @pytest.mark.asyncio
    async def test_download_range(self, provider, file_metadata_object, download_resp, aresponses):
        aresponses.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage' + file_metadata_object.id, 'get', download_resp)

        async with aiohttp.ClientSession() as session:
            stream = await provider.download(session, item=file_metadata_object, range=(0,3))

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name == None
        assert stream.content_type == 'application/octet-stream'
        assert await stream.read() == b'test stream!'


class TestUpload:  #

    @pytest.mark.asyncio
    async def test_upload(self, provider, file_metadata_object, download_resp, aresponses):
        aresponses.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage' + file_metadata_object.id, 'get', download_resp)

        item = await provider.download(item=file_metadata_object)

        assert isinstance(item, OsfMetadata)
