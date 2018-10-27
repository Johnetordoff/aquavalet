import pytest

import io
import os
import zipfile

from aquavalet.core.streams import FileStreamReader, StringStream
from aquavalet.providers.filesystem.metadata import FileSystemMetadata
from aquavalet.core import exceptions

from .fixtures import (
    provider,
    file_metadata,
    folder_metadata,
)

from aquavalet.providers.filesystem import FileSystemProvider


class TestCreateFolder:

    @pytest.mark.asyncio
    async def test_create_folder(self, provider, fs):
        item = await provider.validate_item('/')

        item = await provider.create_folder(item, 'new_folder')

        assert isinstance(item, FileSystemMetadata)
        assert item.name == 'new_folder'
        assert item.path == '/new_folder/'


class TestValidateItem:

    @pytest.mark.asyncio
    async def test_validate_item(self, provider, fs):
        fs.create_dir('test folder/')
        fs.create_file('test folder/test.txt', contents=b'test')

        item = await provider.validate_item('test folder/test.txt')

        assert isinstance(item, FileSystemMetadata)
        assert item.name == 'test.txt'
        assert item.id == 'test folder/test.txt'
        assert item.path == 'test folder/test.txt'
        assert item.kind == 'file'
        assert item.parent == 'test folder/'


    @pytest.mark.asyncio
    async def test_validate_item_root(self, provider, fs):

        item = await provider.validate_item('/')

        assert isinstance(item, FileSystemMetadata)
        assert item.name == 'filesystem root'
        assert item.id == '/'
        assert item.path == '/'
        assert item.kind == 'folder'
        assert item.parent == '/'


    @pytest.mark.asyncio
    async def test_validate_item_not_found(self, provider):
        with pytest.raises(exceptions.NotFoundError) as exc:
            await provider.validate_item('/missing.txt')

        assert exc.value.message == "Item at '/missing.txt' could not be found, folders must end with '/'"


class TestDownload:

    @pytest.mark.asyncio
    async def test_download(self, provider, fs):
        fs.create_dir('test folder/')
        fs.create_file('test folder/test.txt', contents=b'test')


        item = await provider.validate_item('test folder/test.txt')

        stream = await provider.download(item=item)

        isinstance(stream, FileStreamReader)
        assert stream.size == 4

        content = await stream.read()
        assert content == b'test'

    @pytest.mark.asyncio
    async def test_download_range(self, provider, fs):
        fs.create_dir('test folder/')
        fs.create_file('test folder/test.txt', contents=b'test')

        item = await provider.validate_item('test folder/test.txt')

        stream = await provider.download(item=item, range=(0, 1))
        assert stream.partial
        assert stream.size == 2
        assert await stream.read() == b'te'

        stream = await provider.download(item=item, range=(2, 7))
        assert stream.partial
        #assert stream.size == 4
        assert await stream.read() == b'st'

    @pytest.mark.asyncio
    async def test_download_range_open_ended(self, provider):
        item = await provider.validate_item('test folder/flower.jpg')

        stream = await provider.download(item=item, range=(0, None))
        assert not stream.partial
        assert await stream.read() == b'I am a file'

    @pytest.mark.asyncio
    async def test_download_zip(self, provider, setup_filesystem):
        item = await provider.validate_item('test folder/')

        stream = await provider.zip(item, None)

        data = await stream.read()

        zip = zipfile.ZipFile(io.BytesIO(data))

        # Verify CRCs
        assert zip.testzip() is None

        # Check content of included files

        zipped1 = zip.open('subfolder/nested.txt')
        assert zipped1.read() == b'Here is my content'

        zipped2 = zip.open('flower.jpg')
        assert zipped2.read() == b'I am a file'

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
    async def test_delete_root(self, provider, root_metadata):
        with pytest.raises(Exception) as exc:  # TODO find stadard exception
            await provider.delete(root_metadata)

        assert str(exc.value) == "That's the root!"

        assert os.path.exists('/')


    @pytest.mark.asyncio
    async def test_delete_404(self, provider, missing_file_metadata):

        with pytest.raises(exceptions.NotFoundError) as exc:  # temp
            await provider.delete(missing_file_metadata)


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

class TestIntraCopy:

    @pytest.mark.asyncio
    async def test_intra_copy_file(self, provider, file_metadata, folder_metadata, setup_filesystem):
        await provider.intra_copy(file_metadata, folder_metadata)

        item = await provider.validate_item('test folder/subfolder/flower.jpg')

        assert isinstance(item, FileSystemMetadata)
        assert item.path == 'test folder/subfolder/flower.jpg'
        assert item.kind == 'file'
        assert item.name == 'flower.jpg'

        await provider.validate_item('test folder/flower.jpg')  # asserts not deleted


    @pytest.mark.asyncio
    async def test_intra_copy_folder(self, provider, file_metadata, folder_metadata, setup_filesystem):
        await provider.intra_copy(folder_metadata, folder_metadata)

        item = await provider.validate_item('test folder/subfolder/nested.txt')

        assert item.path == 'test folder/subfolder/nested.txt'
        assert item.kind == 'file'
        assert item.name == 'nested.txt'

        await provider.validate_item('test folder/subfolder/nested.txt')  # asserts not deleted


    @pytest.mark.asyncio
    async def test_intra_copy_missiong(self, provider, missing_file_metadata, folder_metadata, setup_filesystem):
        with pytest.raises(exceptions.NotFoundError):
            await provider.intra_copy(missing_file_metadata, folder_metadata)

class TestIntraMove:

    @pytest.mark.asyncio
    async def test_intra_move_file(self, provider, file_metadata, folder_metadata, setup_filesystem):
        await provider.intra_move(file_metadata, folder_metadata)

        item = await provider.validate_item('test folder/subfolder/flower.jpg')

        assert isinstance(item, FileSystemMetadata)
        assert item.path == 'test folder/subfolder/flower.jpg'
        assert item.kind == 'file'
        assert item.name == 'flower.jpg'

        with pytest.raises(exceptions.NotFoundError):
            await provider.validate_item('test folder/flower.jpg')


    @pytest.mark.asyncio
    async def test_intra_move_folder(self, provider, folder_metadata, setup_filesystem):
        await provider.intra_move(folder_metadata, folder_metadata)

        item = await provider.validate_item('test folder/other_subfolder/')

        assert item.path == 'test folder/other_subfolder/'
        assert item.kind == 'folder'
        assert item.name == 'other_subfolder'

        with pytest.raises(exceptions.NotFoundError):
            await provider.validate_item('test folder/other_subfolder/flower.jpg')

    @pytest.mark.asyncio
    async def test_intra_move_missing(self, provider, missing_file_metadata, folder_metadata, setup_filesystem):
        with pytest.raises(exceptions.NotFoundError):
            await provider.intra_move(missing_file_metadata, folder_metadata, provider)


class TestRename:

    @pytest.mark.asyncio
    async def test_rename(self, provider, file_metadata):
        await provider.rename(file_metadata, 'new_name')

        item = await provider.validate_item('test folder/new_name')

        assert isinstance(item, FileSystemMetadata)
        assert item.path == 'test folder/new_name'
        assert item.kind == 'file'
        assert item.name == 'new_name'

    @pytest.mark.asyncio
    async def test_rename_missing(self, provider, missing_file_metadata):
        with pytest.raises(exceptions.NotFoundError):
            await provider.rename(missing_file_metadata, 'new_name')

class TestOperations:

    def test_can_intra_copy(self, provider):
        assert provider.can_intra_copy(provider)

    def test_can_intra_move(self, provider):
        assert provider.can_intra_move(provider)
