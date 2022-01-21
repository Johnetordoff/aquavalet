import pytest
import aiohttp

from aquavalet.providers.osfstorage.metadata import OsfMetadata
from aquavalet.streams.http import ResponseStreamReader
from aquavalet.exceptions import InvalidPathError, NotFoundError

from tests.core.test_provider import BaseProviderTestSuite


from tests.providers.osfstorage.fixtures import (
    from_fixture_json,
)

from tests.streams.fixtures import RequestStreamFactory

from tests.providers.osfstorage.utils import MockOsfstorageServer
from aquavalet.providers.osfstorage.provider import OSFStorageProvider

import asyncio
import functools


def mocked_server(func):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def wrapper(*args, **kwargs):
        self = args[0]
        args = list(args)
        with self.mock_server() as server:
            provider = self.provider({})
            provider.internal_provider = "osfstorage"
            provider.resource = "guid0"

            args.append(server)
            args.append(provider)
            return await func(*args, **kwargs)

    return wrapper


class TestOsfStorageProvider(BaseProviderTestSuite):

    provider = OSFStorageProvider
    mock_server = MockOsfstorageServer

    @pytest.mark.asyncio
    async def test_validate_item_no_internal_provider(self, provider):

        with pytest.raises(InvalidPathError) as exc:
            await provider.validate_item("/badpath")

        assert exc.value.message == "match could not be found"

        with pytest.raises(InvalidPathError) as exc:
            await provider.validate_item("/badpath/")

        assert exc.value.message == "match could not be found"

        with pytest.raises(InvalidPathError):
            await provider.validate_item("/badpath/das")

        assert exc.value.message == "match could not be found"

        with pytest.raises(InvalidPathError):
            await provider.validate_item("/badpath/guid0")

        assert exc.value.message == "match could not be found"

    @pytest.mark.asyncio
    async def test_validate_item_404(self, provider):
        self.m
        with pytest.raises(NotFoundError) as exc:
            await provider.validate_item("/osfstorage/guid0/not-root")

        assert (
            exc.value.message
            == "Item at 'Item at path 'not' cannot be found.' could not be found, folders must end with '/'"
        )

    @pytest.mark.asyncio
    async def test_validate_item_root(self, provider):
        item = await provider.validate_item("/osfstorage/guid0/")

        assert isinstance(item, OsfMetadata)

        assert item.id == "/"
        assert item.path == "/"
        assert item.name == "osfstorage root"
        assert item.kind == "folder"
        assert item.mimetype is None

    @mocked_server
    @pytest.mark.asyncio
    async def test_validate_item(self, server, provider):
        file_metadata = server.get_file_json()
        server.mock_metadata(file_metadata)
        item = await provider.validate_item(
            "/osfstorage/guid0/5b6ee0c390a7e0001986aff5/"
        )

        assert isinstance(item, OsfMetadata)

        assert item.id == "/5b6ee0c390a7e0001986aff5"
        assert item.path == "/5b6ee0c390a7e0001986aff5"
        assert item.name == "test.txt"
        assert item.kind == "file"
        assert item.mimetype == "text/plain"

    @mocked_server
    @pytest.mark.asyncio
    async def test_metadata(self, server, provider):
        file_item = server.get_file_item()
        item = await provider.metadata(file_item)

        assert isinstance(item, OsfMetadata)

        assert item.id == "/5b6ee0c390a7e0001986aff5"
        assert item.path == "/5b6ee0c390a7e0001986aff5"
        assert item.name == "test.txt"
        assert item.kind == "file"
        assert item.mimetype == "text/plain"

    @mocked_server
    @pytest.mark.asyncio
    async def test_versions(self, server, provider):
        file_json = server.get_file_json()
        file_item = server.get_file_item()

        server.mock_versions(file_json, from_fixture_json("versions_metadata"))

        versions = await provider.versions(file_item)

        assert isinstance(versions, list)
        assert len(versions) == 2

        item = versions[0]
        assert item.id == "/5b6ee0c390a7e0001986aff5"
        assert item.path == "/5b6ee0c390a7e0001986aff5"
        assert item.name == "test.txt"
        assert item.kind == "file"
        assert item.mimetype == "text/plain"

    @mocked_server
    @pytest.mark.asyncio
    async def test_download(self, server, provider):
        file_json = server.get_file_json()
        item = server.get_file_item()

        server.mock_download(file_json, "test stream!")

        async with aiohttp.ClientSession() as session:
            stream = await provider.download(item, session)

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name is None
        assert stream.content_type == "application/octet-stream"
        assert await stream.read() == b"test stream!"

    @mocked_server
    @pytest.mark.asyncio
    async def test_download_range(self, server, provider):
        file_json = server.get_file_json()
        item = server.get_file_item()
        server.mock_download(file_json, b"test stream!")

        async with aiohttp.ClientSession() as session:
            stream = await provider.download(item, session, range=(0, 3))

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name is None
        assert stream.content_type == "application/octet-stream"
        assert (
            await stream.read() == b"test stream!"
        )  # this should really be truncated, but it's done by osf which is mocked.

    @mocked_server
    @pytest.mark.asyncio
    async def test_download_version(self, server, provider):
        file_json = server.get_file_json()
        item = server.get_file_item()
        server.mock_download_version(file_json, b"test stream!")

        async with aiohttp.ClientSession() as session:
            stream = await provider.download(item, session, version=2)

        assert isinstance(stream, ResponseStreamReader)
        assert stream.size == 12
        assert stream.name is None
        assert stream.content_type == "application/octet-stream"
        assert await stream.read() == b"test stream!"

    @mocked_server
    @pytest.mark.asyncio
    async def test_upload(self, server, provider):
        file_json = server.get_file_json()
        file_item = server.get_file_item()
        stream = RequestStreamFactory()

        server.mock_upload(file_json)
        item = await provider.upload(item=file_item, stream=stream, new_name="test.txt")

        assert isinstance(item, OsfMetadata)
        assert item.name == "test.txt"
        assert item.mimetype == "text/plain"

    @mocked_server
    @pytest.mark.asyncio
    async def test_delete(self, server, provider):
        file_json = server.get_file_json()
        file_item = server.get_file_item()
        server.mock_delete(file_json)
        item = await provider.delete(file_item)

        assert item is None

    @mocked_server
    @pytest.mark.asyncio
    async def test_create_folder(self, server, provider):
        folder_json = server.get_folder_json()
        folder_item = server.get_folder_item()

        server.mock_create_folder(folder_json)
        item = await provider.create_folder(folder_item, "new_test_folder")

        assert isinstance(item, OsfMetadata)
        assert item.name == "test_folder"  #  technically wrong mocking
        assert item.mimetype is None

    @mocked_server
    @pytest.mark.asyncio
    async def test_intra_copy(self, server, provider):
        file_item = server.get_file_item()

        item = await provider.intra_copy(file_item, file_item, provider)

        assert item is None

    @mocked_server
    @pytest.mark.asyncio
    async def test_rename(self, server, provider):
        file_json = server.get_file_json()
        file_item = server.get_file_item()

        server.mock_rename(file_json)
        item = await provider.rename(file_item, "new_name")

        assert isinstance(item, OsfMetadata)
        assert item.path == "/5b8d55ae6a59a50017708986"
        assert item.kind == "file"
        assert (
            item.name == "test.txt"
        )  # this should really be 'new_name, but it's done by osf which is mocked.

    @mocked_server
    @pytest.mark.asyncio
    async def test_children(self, server, provider):
        folder_json = server.get_folder_json()
        children_json = server.get_children_json()
        folder_item = server.get_folder_item()

        server.mock_metadata(folder_json)
        server.mock_children(folder_json, children_metadata=children_json)

        item = await provider.children(folder_item)

        assert isinstance(item, list)
        assert len(item) == 2
        assert item[0].path == "/5b5de758f63e210010ec8f53/"
        assert item[0].name == "test_folder"
        assert item[0].kind == "folder"
        assert item[1].path == "/5b6ee0c390a7e0001986aff5"
        assert item[1].name == "test.txt"
        assert item[1].kind == "file"

    @mocked_server
    @pytest.mark.asyncio
    async def test_download_zip(self, server, provider):
        pass
