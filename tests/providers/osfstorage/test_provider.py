import pytest
import aiohttp

from aquavalet.providers.osfstorage.metadata import OsfMetadata
from aquavalet.streams.http import ResponseStreamReader
from aquavalet.exceptions import (
    InvalidPathError,
    NotFoundError
)

from tests.core.test_provider import BaseProviderTestSuite


from tests.providers.osfstorage.fixtures import (
    provider,
    file_metadata_resp,
    folder_metadata_object,
    folder_metadata_resp,
    response_404,
    file_metadata_object,
    file_metadata_json,
    children_resp,
    create_folder_resp,
    create_folder_response_json,
    folder_metadata_json,
    delete_resp,
    upload_resp,
    download_resp,
    mock_file_metadata,
    mock_version_metadata,
    mock_file_upload,
    mock_file_missing,
    mock_file_delete,
    mock_create_folder,
    mock_children,
    mock_rename,
    mock_intra_copy,
    from_fixture_json,
)

from tests.streams.fixtures import (
    RequestStreamFactory
)

from tests.providers.osfstorage.utils import MockOsfstorageServer
from aquavalet.providers.osfstorage.provider import OSFStorageProvider

def mock_server(func):
    async def wrapper(*args, **kwargs):
        self = args[0]
        args = list(args)
        async with self.mock_server2() as server:
            provider = self.provider({})
            provider.internal_provider = 'osfstorage'
            provider.resource = 'guid0'
            args.append(server)
            args.append(provider)
            return await func(*args, **kwargs)
    return wrapper


class TestOsfStorageProvider(BaseProviderTestSuite):

    provider = OSFStorageProvider
    mock_server2 = MockOsfstorageServer

    @pytest.mark.asyncio
    async def test_validate_item_no_internal_provider(self, provider, mock_file_metadata):

        with pytest.raises(InvalidPathError) as exc:
            await provider.validate_item('/badpath')

        assert exc.value.message == 'match could not be found'

        with pytest.raises(InvalidPathError) as exc:
            await provider.validate_item('/badpath/')

        assert exc.value.message == 'match could not be found'

        with pytest.raises(InvalidPathError):
            await provider.validate_item('/badpath/das')

        assert exc.value.message == 'match could not be found'

        with pytest.raises(InvalidPathError):
            await provider.validate_item('/badpath/guid0')

        assert exc.value.message == 'match could not be found'

    @pytest.mark.asyncio
    async def test_validate_item_404(self, provider, mock_file_missing):

        with pytest.raises(NotFoundError) as exc:
            await provider.validate_item('/osfstorage/guid0/not-root')

        assert exc.value.message == "Item at 'Item at path 'not' cannot be found.' could not be found, folders must end with '/'"


    @pytest.mark.asyncio
    async def test_validate_item_root(self, provider):
        item = await provider.validate_item('/osfstorage/guid0/')

        assert isinstance(item, OsfMetadata)

        assert item.id == '/'
        assert item.path == '/'
        assert item.name == 'osfstorage root'
        assert item.kind == 'folder'
        assert item.mimetype is None

    @mock_server
    @pytest.mark.asyncio
    async def test_validate_item(self, server, provider):
        server.mock_metadata(file_metadata_json())
        item = await provider.validate_item('/osfstorage/guid0/5b6ee0c390a7e0001986aff5/')

        assert isinstance(item, OsfMetadata)

        assert item.id == '/5b6ee0c390a7e0001986aff5'
        assert item.path == '/5b6ee0c390a7e0001986aff5'
        assert item.name == 'test.txt'
        assert item.kind == 'file'
        assert item.mimetype == 'text/plain'

    @pytest.mark.asyncio
    async def test_metadata(self, provider, file_metadata_json):
        async with self.MockServer() as server:
            server.mock_metadata(file_metadata_json)
            item = await provider.validate_item('/osfstorage/guid0/5b6ee0c390a7e0001986aff5/')
            item = await provider.metadata(item)

        assert isinstance(item, OsfMetadata)

        assert item.id == '/5b6ee0c390a7e0001986aff5'
        assert item.path == '/5b6ee0c390a7e0001986aff5'
        assert item.name == 'test.txt'
        assert item.kind == 'file'
        assert item.mimetype == 'text/plain'

    @pytest.mark.asyncio
    async def test_versions(self, provider, file_metadata_json):
        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata_json)
            server.mock_versions(file_metadata_json, from_fixture_json('versions_metadata'))
            item = await provider.validate_item(f'/osfstorage/guid0/{file_metadata_json["data"]["id"]}')
            versions = await provider.versions(item)

        assert isinstance(versions, list)
        assert len(versions) == 2

        item = versions[0]
        assert item.id == '/5b6ee0c390a7e0001986aff5'
        assert item.path == '/5b6ee0c390a7e0001986aff5'
        assert item.name == 'test.txt'
        assert item.kind == 'file'
        assert item.mimetype == 'text/plain'

    @pytest.mark.asyncio
    async def test_download(self, provider, file_metadata_json, file_metadata_object):
        async with MockOsfstorageServer() as server:
            server.mock_download(file_metadata_json, b'test stream!')

            async with aiohttp.ClientSession() as session:
                stream = await provider.download(file_metadata_object, session)

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name == None
        assert stream.content_type == 'application/octet-stream'
        assert await stream.read() == b'test stream!'

    @pytest.mark.asyncio
    async def test_download_range(self, provider, file_metadata_object, file_metadata_json):
        async with MockOsfstorageServer() as server:
            server.mock_download(file_metadata_json, b'test stream!')

            async with aiohttp.ClientSession() as session:
                stream = await provider.download(file_metadata_object, session, range=(0,3))

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name == None
        assert stream.content_type == 'application/octet-stream'
        assert await stream.read() == b'test stream!'  # this should really be truncated, but it's done by osf which is mocked.

    @pytest.mark.asyncio
    async def test_download_version(self, provider, file_metadata_object, file_metadata_json):
        async with MockOsfstorageServer() as server:
            server.mock_download_version(file_metadata_json, b'test stream!')

            async with aiohttp.ClientSession() as session:
                stream = await provider.download(file_metadata_object, session, version=2)

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name == None
        assert stream.content_type == 'application/octet-stream'
        assert await stream.read() == b'test stream!'

    @pytest.mark.asyncio
    async def test_upload(self, provider, file_metadata_object, file_metadata_json):
        async with MockOsfstorageServer() as server:
            server.mock_upload(file_metadata_json)
            item = await provider.upload(item=file_metadata_object, stream=RequestStreamFactory(), new_name='test.txt')

        assert isinstance(item, OsfMetadata)
        assert item.name == 'test.txt'
        assert item.mimetype == 'text/plain'

    @pytest.mark.asyncio
    async def test_delete(self, provider, file_metadata_object, file_metadata_json):
        async with MockOsfstorageServer() as server:
            server.mock_delete(file_metadata_json)
            item = await provider.delete(file_metadata_object)

        assert item is None

    @pytest.mark.asyncio
    async def test_create_folder(self, provider, folder_metadata_object, folder_metadata_json):
        async with MockOsfstorageServer() as server:
            server.mock_create_folder(folder_metadata_json)
            item = await provider.create_folder(folder_metadata_object, 'new_test_folder')

        assert isinstance(item, OsfMetadata)
        assert item.name == 'test_folder'  #  technically wrong mocking
        assert item.mimetype is None

    @pytest.mark.asyncio
    async def test_intra_copy(self, provider, file_metadata_object, mock_intra_copy):

        item = await provider.intra_copy(file_metadata_object, file_metadata_object, provider)

        assert item is None

    @pytest.mark.asyncio
    async def test_rename(self, provider, file_metadata_object, file_metadata_json):
        async with MockOsfstorageServer() as server:
            server.mock_rename(file_metadata_json)
            item = await provider.rename(file_metadata_object, 'new_name')

        assert isinstance(item, OsfMetadata)
        assert item.path == '/5b6ee0c390a7e0001986aff5'
        assert item.kind == 'file'
        assert item.name == 'test.txt'  # this should really be 'new_name, but it's done by osf which is mocked.

    @pytest.mark.asyncio
    async def test_children(self, provider, folder_metadata_object, file_metadata_json):
        async with MockOsfstorageServer() as server:
            server.mock_children(folder_metadata_json, children_metadata=False)

            item = await provider.children(folder_metadata_object)

        assert isinstance(item, list)
        assert len(item) == 2
        assert item[0].path == '/5b5de758f63e210010ec8f53/'
        assert item[0].name == 'test_folder'
        assert item[0].kind == 'folder'
        assert item[1].path == '/5b6ee0c390a7e0001986aff5'
        assert item[1].name == 'test.txt'
        assert item[1].kind == 'file'

    @pytest.mark.asyncio
    async def test_download_zip(self, provider, folder_metadata_object):

        item = await provider.children(folder_metadata_object)
