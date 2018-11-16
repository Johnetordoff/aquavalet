import pytest
import aiohttp

from aquavalet.providers.osfstorage.metadata import OsfMetadata
from aquavalet.streams.http import ResponseStreamReader
from aquavalet.exceptions import (
    InvalidPathError,
    NotFoundError
)

from tests.providers.osfstorage.fixtures import (
    provider,
    file_metadata_resp,
    folder_metadata_object,
    folder_metadata_resp,
    response_404,
    response_404_json,
    file_metadata_object,
    file_metadata_json,
    children_resp,
    create_folder_resp,
    create_folder_response_json,
    delete_resp,
    upload_resp,
    download_resp,
    mock_file_metadata,
    mock_file_download,
    mock_file_upload,
    mock_file_missing,
    mock_file_delete,
    mock_create_folder,
    mock_children,
    mock_rename,
    mock_intra_copy
)

from tests.streams.fixtures import (
    request_stream
)

import json
from aiohttp.web import Response


class TestValidateItem:

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

    @pytest.mark.asyncio
    async def test_validate_item(self, provider, mock_file_metadata):
        item = await provider.validate_item('/osfstorage/guid0/5b6ee0c390a7e0001986aff5/')

        assert isinstance(item, OsfMetadata)

        assert item.id == '/5b6ee0c390a7e0001986aff5'
        assert item.path == '/5b6ee0c390a7e0001986aff5'
        assert item.name == 'test.txt'
        assert item.kind == 'file'
        assert item.mimetype == 'text/plain'


class TestDownload:

    @pytest.mark.asyncio
    async def test_download(self, provider, file_metadata_object, mock_file_download):

        async with aiohttp.ClientSession() as session:
            stream = await provider.download(file_metadata_object, session)

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name == None
        assert stream.content_type == 'application/octet-stream'
        assert await stream.read() == b'test stream!'

    @pytest.mark.asyncio
    async def test_download_range(self, provider, file_metadata_object, mock_file_download):

        async with aiohttp.ClientSession() as session:
            stream = await provider.download(file_metadata_object, session, range=(0,3))

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name == None
        assert stream.content_type == 'application/octet-stream'
        assert await stream.read() == b'test stream!'  # this should really be truncated, but it's done by osf which is mocked.


class TestUpload:

    @pytest.mark.asyncio
    async def test_upload(self, provider, file_metadata_object, request_stream, mock_file_upload):

        item = await provider.upload(item=file_metadata_object, stream=request_stream, new_name='test.txt')

        assert isinstance(item, OsfMetadata)
        assert item.name == 'test.txt'
        assert item.mimetype == 'text/plain'


class TestDelete:

    @pytest.mark.asyncio
    async def test_delete(self, provider, file_metadata_object, mock_file_delete):

        item = await provider.delete(file_metadata_object)

        assert item is None


class TestCreateFolder:

    @pytest.mark.asyncio
    async def test_create_folder(self, provider, file_metadata_object, mock_create_folder):

        item = await provider.create_folder(file_metadata_object, 'test')

        assert isinstance(item, OsfMetadata)
        assert item.name == 'test'
        assert item.mimetype is None


class TestIntraCopy:

    @pytest.mark.asyncio
    async def test_intra_copy(self, provider, file_metadata_object, mock_intra_copy):

        item = await provider.intra_copy(file_metadata_object, file_metadata_object, provider)

        assert item is None


class TestRename:

    @pytest.mark.asyncio
    async def test_rename(self, provider, file_metadata_object, mock_rename):
        item = await provider.rename(file_metadata_object, 'new_name')

        assert isinstance(item, OsfMetadata)
        assert item.path == '/5b6ee0c390a7e0001986aff5'
        assert item.kind == 'file'
        assert item.name == 'test.txt'  # this should really be 'new_name, but it's done by osf which is mocked.


class TestChildren:

    @pytest.mark.asyncio
    async def test_children(self, provider, folder_metadata_object, mock_children):

        item = await provider.children(folder_metadata_object)

        assert isinstance(item, list)
        assert len(item) == 2
        assert item[0].path == '/5b537030c86a8c001243ce7a'
        assert item[0].name == 'test-1'
        assert item[0].kind == 'file'
        assert item[1].path == '/5b4247025b38c4001068a7b6/'
        assert item[1].name == 'test-2'
        assert item[1].kind == 'folder'

