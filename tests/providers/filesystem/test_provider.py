import pytest

import io
import os
from http import client

from aquavalet.core.streams import FileStreamReader, StringStream
from aquavalet.providers.filesystem.metadata import FileSystemMetadata
from aquavalet.core import exceptions

from .fixtures import (
    provider,
    setup_filesystem
)

from aquavalet.providers.filesystem import FileSystemProvider


class TestValidateItem:

    @pytest.mark.asyncio
    async def test_validate_item(self, provider, setup_filesystem):

        item = await provider.validate_item('test folder/flower.jpg')

        assert isinstance(item, FileSystemMetadata)
        assert item.name == 'flower.jpg'
        assert item.id == 'test folder/flower.jpg'
        assert item.path == 'test folder/flower.jpg'
        assert item.kind == 'file'
        assert item.parent == 'test folder/'


    @pytest.mark.asyncio
    async def test_validate_item_not_found(self, provider):
        with pytest.raises(exceptions.NotFoundError) as exc:
            await provider.validate_item('/missing.txt')

        assert exc.value.message == "Item at '/missing.txt' could not be found, folders must end with '/'"

class TestDownload:

    @pytest.mark.asyncio
    async def test_download(self, provider, setup_filesystem):
        item = await provider.validate_item('test folder/flower.jpg')

        stream = await provider.download(item=item)

        isinstance(stream, FileStreamReader)
        assert stream.size == 11

        content = await stream.read()
        assert content == b'I am a file'

    @pytest.mark.asyncio
    async def test_download_range(self, provider):
        item = await provider.validate_item('test folder/flower.jpg')

        stream = await provider.download(item=item, range=(0, 1))
        assert stream.partial
        assert stream.size == 2
        assert await stream.read() == b'I '

        stream = await provider.download(item=item, range=(2, 5))
        assert stream.partial
        assert stream.size == 4
        assert await stream.read() == b'am a'

    @pytest.mark.asyncio
    async def test_download_range_open_ended(self, provider):
        item = await provider.validate_item('test folder/flower.jpg')

        stream = await provider.download(item=item, range=(0, None))
        assert not stream.partial
        assert await stream.read() == b'I am a file'

    @pytest.mark.asyncio
    async def test_download_zip(self, provider):
        item = await provider.validate_item('test folder/')

        stream = await provider.zip(None, item=item)
        assert await stream.read() == b'I am a file'


class TestUpload:

    @pytest.mark.asyncio
    async def test_upload(self, provider):
        item = await provider.validate_item('test folder/')

        file_content = b'Test Upload Content'
        file_stream = StringStream(file_content)

        await provider.upload(stream=file_stream, item=item, new_name='upload.txt')

        item = await provider.validate_item('test folder/upload.txt')

        assert item.name == 'upload.txt'
        assert item.path == 'test folder/upload.txt'
        assert item.size == len(file_content)


class TestDelete:

    @pytest.mark.asyncio
    async def test_delete_file(self, provider, setup_filesystem):
        item = await provider.validate_item('test folder/flower.jpg')

        await provider.delete(item=item)

        with pytest.raises(exceptions.NotFoundError):
            await provider.validate_item('test folder/flower.jpg')

    @pytest.mark.asyncio
    async def test_delete_folder(self, provider):
        item = await provider.validate_item('test folder/subfolder/')

        await provider.delete(item=item)

        with pytest.raises(exceptions.NotFoundError):
            await provider.validate_item('test folder/subfolder/')

    @pytest.mark.asyncio
    async def test_delete_root(self, provider):
        path = await provider.validate_item('/')

        with pytest.raises(Exception) as exc:  # temp
            await provider.delete(path)

        assert str(exc.value) == "That's the root!"

        assert os.path.exists('/')


class TestChildren:

    @pytest.mark.asyncio
    async def test_children(self, provider):
        item = await provider.validate_item('test folder/')
        children = await provider.children(item=item)

        assert isinstance(children, list)
        assert len(children) == 3

        file = next(x for x in children if x.kind == 'file')
        assert file.name == 'flower.jpg'
        assert file.path == 'test folder/flower.jpg'
        folder = next(x for x in children if x.kind == 'folder')
        assert folder.name == 'subfolder' or 'other_subfolder'
        assert folder.path == 'test folder/subfolder/' or 'test folder/other_subfolder/'


class TestMetadata:
    """
    The metadata method doesn't really exist in this provider, so these tests are just here for no  reason.
    """

    @pytest.mark.asyncio
    async def test_metadata_file(self, provider):
        item = await provider.validate_item('test folder/flower.jpg')

        assert isinstance(item, FileSystemMetadata)
        assert item.kind == 'file'
        assert item.name == 'flower.jpg'
        assert item.path == 'test folder/flower.jpg'

    @pytest.mark.asyncio
    async def test_metadata_folder(self, provider):
        item = await provider.validate_item('test folder/subfolder/')

        assert isinstance(item, FileSystemMetadata)
        assert item.kind == 'folder'
        assert item.name == 'subfolder'
        assert item.path == 'test folder/subfolder/'

    @pytest.mark.asyncio
    async def test_metadata_missing(self, provider):

        with pytest.raises(exceptions.NotFoundError):
            await provider.validate_item('/missing.txt')


class TestIntra:

    @pytest.mark.asyncio
    async def test_intra_copy_file(self, provider, setup_filesystem):
        src_item = await provider.validate_item('test folder/flower.jpg')
        dest_item = await provider.validate_item('test folder/subfolder/')

        await provider.intra_copy(provider, src_item, dest_item)

        item = await provider.validate_item('test folder/subfolder/flower.jpg')

        assert isinstance(item, FileSystemMetadata)
        assert item.path == 'test folder/subfolder/flower.jpg'
        assert item.kind == 'file'
        assert item.name == 'flower.jpg'

        await provider.validate_item('test folder/flower.jpg')  # asserts not deleted

    @pytest.mark.asyncio
    async def test_intra_move_file(self, provider, setup_filesystem):
        src_item = await provider.validate_item('test folder/flower.jpg')
        dest_item = await provider.validate_item('test folder/subfolder/')

        await provider.intra_move(provider, src_item, dest_item)

        item = await provider.validate_item('test folder/subfolder/flower.jpg')

        assert isinstance(item, FileSystemMetadata)
        assert item.path == 'test folder/subfolder/flower.jpg'
        assert item.kind == 'file'
        assert item.name == 'flower.jpg'

        with pytest.raises(exceptions.NotFoundError):
            await provider.validate_item('test folder/flower.jpg')


    @pytest.mark.asyncio
    async def test_intra_move_folder(self, provider):
        src_item = await provider.validate_item('test folder/subfolder/')
        dest_item = await provider.validate_item('test folder/other_subfolder/')

        await provider.intra_move(provider, src_item, dest_item)

        item = await provider.validate_item('test folder/other_subfolder/subfolder/nested.txt')

        assert item.path == 'test folder/other_subfolder/subfolder/nested.txt'
        assert item.kind == 'file'
        assert item.name == 'nested.txt'


class TestInter:
    pass


class TestOperations:

    def test_can_intra_copy(self, provider):
        assert provider.can_intra_copy(provider)

    def test_can_intra_move(self, provider):
        assert provider.can_intra_move(provider)
