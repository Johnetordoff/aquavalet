import pytest

import io
import os
import zipfile

from aquavalet.streams.file import FileStreamReader
from aquavalet.providers.filesystem.metadata import FileSystemMetadata
from aquavalet import exceptions

from .fixtures import missing_file_metadata, provider

from tests.streams.fixtures import RequestStreamFactory


class TestCreateFolder:
    @pytest.mark.gen_test
    async def test_create_folder(self, provider, fs):
        item = await provider.validate_item("/")

        item = await provider.create_folder(item, "new_folder")

        assert isinstance(item, FileSystemMetadata)
        assert item.name == "new_folder"
        assert item.path == "/new_folder/"


class TestValidateItem:
    @pytest.mark.gen_test
    async def test_validate_item(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test folder/test.txt", contents=b"test")

        item = await provider.validate_item("test folder/test.txt")

        assert isinstance(item, FileSystemMetadata)
        assert item.name == "test.txt"
        assert item.id == "test folder/test.txt"
        assert item.path == "test folder/test.txt"
        assert item.kind == "file"
        assert item.parent == "test folder/"

    @pytest.mark.gen_test
    async def test_validate_item_root(self, provider, fs):

        item = await provider.validate_item("/")

        assert isinstance(item, FileSystemMetadata)
        assert item.name == "filesystem root"
        assert item.id == "/"
        assert item.path == "/"
        assert item.kind == "folder"
        assert item.parent == "/"

    @pytest.mark.gen_test
    async def test_validate_item_not_found(self, provider):
        with pytest.raises(exceptions.NotFoundError) as exc:
            await provider.validate_item("/missing.txt")

        assert (
            exc.value.message
            == "Item at 'Item at '/missing.txt' could not be found, folders must end with '/'' could not be found, folders must end with '/'"
        )


class TestDownload:
    @pytest.mark.gen_test
    async def test_download(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test folder/test.txt", contents=b"test")

        item = await provider.validate_item("test folder/test.txt")

        stream = await provider.download(item=item)

        isinstance(stream, FileStreamReader)
        assert stream.size == 4

        content = await stream.read()
        assert content == b"test"

    @pytest.mark.gen_test
    async def test_download_range(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test folder/test.txt", contents=b"test")

        item = await provider.validate_item("test folder/test.txt")

        stream = await provider.download(item=item, range=(0, 1))
        assert stream.size == 2
        assert await stream.read() == b"te"

        stream = await provider.download(item=item, range=(2, 7))
        assert stream.size == 6
        assert await stream.read() == b"st"

    @pytest.mark.gen_test
    async def test_download_range_open_ended(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test folder/test.txt", contents=b"test")

        item = await provider.validate_item("test folder/test.txt")

        stream = await provider.download(item=item, range=(0, None))
        assert await stream.read() == b"test"

    @pytest.mark.gen_test
    async def test_download_zip(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_dir("test folder/test folder 2/")
        fs.create_file("test folder/test-1.txt", contents=b"test-1")
        fs.create_file("test folder/test folder 2/test-2.txt", contents=b"test-2")

        item = await provider.validate_item("test folder/")

        stream = await provider.zip(item, None)

        data = b""
        async for chunk in stream:
            data += chunk

        zip = zipfile.ZipFile(io.BytesIO(data))

        # Verify CRCs
        assert zip.testzip() is None

        # Check content of included files
        zipped1 = zip.open("test-1.txt")
        assert zipped1.read() == b"test-1"

        zipped1 = zip.open("test folder 2/test-2.txt")
        assert zipped1.read() == b"test-2"


class TestUpload:
    @pytest.mark.gen_test
    async def test_upload(self, provider, fs):
        fs.create_dir("test folder/")
        item = await provider.validate_item("test folder/")
        await provider.upload(
            stream=RequestStreamFactory(), item=item, new_name="upload.txt"
        )

        item = await provider.validate_item("test folder/upload.txt")

        assert item.name == "upload.txt"
        assert item.path == "test folder/upload.txt"
        assert item.size == 9

    @pytest.mark.gen_test
    async def test_upload_warn(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test folder/upload.txt")

        item = await provider.validate_item("test folder/")

        with pytest.raises(exceptions.Conflict):
            await provider.upload(
                stream=RequestStreamFactory(),
                item=item,
                new_name="upload.txt",
                conflict="warn",
            )

        with pytest.raises(exceptions.Conflict):
            await provider.upload(
                stream=RequestStreamFactory(), item=item, new_name="upload.txt"
            )

    @pytest.mark.gen_test
    async def test_upload_replace(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test folder/upload.txt", contents=b"1234")

        item = await provider.validate_item("test folder/")

        await provider.upload(
            stream=RequestStreamFactory(),
            item=item,
            new_name="upload.txt",
            conflict="replace",
        )

        item = await provider.validate_item("test folder/upload.txt")

        stream = await provider.download(item=item)
        assert await stream.read() == b"test data"

    @pytest.mark.gen_test
    async def test_upload_new_version(self):
        """Not possible in filesystem"""
        pass

    @pytest.mark.gen_test
    async def test_upload_rename(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test folder/upload.txt")

        item = await provider.validate_item("test folder/")

        await provider.upload(
            stream=RequestStreamFactory(),
            item=item,
            new_name="upload.txt",
            conflict="rename",
        )
        await provider.validate_item("test folder/upload(1).txt")

        await provider.upload(
            stream=RequestStreamFactory(),
            item=item,
            new_name="upload.txt",
            conflict="rename",
        )
        await provider.validate_item("test folder/upload(2).txt")


class TestDelete:
    @pytest.mark.gen_test
    async def test_delete_file(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test folder/text.txt")

        item = await provider.validate_item("test folder/text.txt")

        await provider.delete(item=item)

        with pytest.raises(exceptions.NotFoundError):
            await provider.validate_item("test folder/text.txt")

    @pytest.mark.gen_test
    async def test_delete_folder(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_dir("test folder/test folder 2/")

        item = await provider.validate_item("test folder/test folder 2/")

        await provider.delete(item=item)

        with pytest.raises(exceptions.NotFoundError):
            await provider.validate_item("test folder/test folder 2/")

    @pytest.mark.gen_test
    async def test_delete_root(self, provider, fs):
        root = await provider.validate_item("/")

        with pytest.raises(Exception) as exc:  # TODO find stadard exception
            await provider.delete(root)

        assert str(exc.value) == "That's the root!"

        assert os.path.exists("/")

    @pytest.mark.gen_test
    async def test_delete_404(self, provider, fs, missing_file_metadata):

        with pytest.raises(exceptions.NotFoundError) as exc:  # temp
            await provider.delete(missing_file_metadata)


class TestChildren:
    @pytest.mark.gen_test
    async def test_children(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_dir("test folder/test folder 2/")
        fs.create_file("test folder/text-1.txt")
        fs.create_file("test folder/text-2.txt")
        fs.create_file("test folder/text-3.txt")

        item = await provider.validate_item("test folder/")
        children = await provider.children(item=item)

        assert isinstance(children, list)
        assert len(children) == 4

        files = [x for x in children if x.kind == "file"]
        assert len(files) == 3
        file = files[0]
        assert file.name in ("text-1.txt", "text-2.txt", "text-3.txt")
        assert file.path in (
            "test folder/text-1.txt",
            "test folder/text-2.txt",
            "test folder/text-3.txt",
        )
        folder = [x for x in children if x.kind == "folder"][0]
        assert folder.name == "test folder 2"
        assert folder.path == "test folder/test folder 2/"


class TestMetadata:
    """
    The metadata method doesn't really exist in this provider, so these tests are just here for no reason.
    """

    @pytest.mark.gen_test
    async def test_metadata_file(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test folder/text-1.txt")

        item = await provider.validate_item("test folder/text-1.txt")
        item2 = await provider.metadata(item)
        assert item == item2

    @pytest.mark.gen_test
    async def test_validate_item_file(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test folder/text-1.txt")

        item = await provider.validate_item("test folder/text-1.txt")

        assert isinstance(item, FileSystemMetadata)
        assert item.kind == "file"
        assert item.name == "text-1.txt"
        assert item.path == "test folder/text-1.txt"
        assert item.mime_type == "text/plain"
        assert item.modified
        assert item.etag

    @pytest.mark.gen_test
    async def test_validate_item_folder(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_dir("test folder/subfolder/")

        item = await provider.validate_item("test folder/subfolder/")

        assert isinstance(item, FileSystemMetadata)
        assert item.kind == "folder"
        assert item.name == "subfolder"
        assert item.path == "test folder/subfolder/"
        assert item.modified
        assert item.etag
        assert not item.mime_type


class TestIntraCopy:
    @pytest.mark.gen_test
    async def test_intra_copy_file(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test.txt")

        folder = await provider.validate_item("test folder/")
        file = await provider.validate_item("test.txt")

        await provider.intra_copy(file, folder)

        item = await provider.validate_item("test folder/test.txt")

        assert isinstance(item, FileSystemMetadata)
        assert item.path == "test folder/test.txt"
        assert item.kind == "file"
        assert item.name == "test.txt"

        await provider.validate_item("test.txt")  # asserts copied not deleted

    @pytest.mark.gen_test
    async def test_intra_copy_folder(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_dir("test folder 2/")
        fs.create_file("test folder/test.txt")

        folder = await provider.validate_item("test folder/")
        folder2 = await provider.validate_item("test folder 2/")
        await provider.intra_copy(folder, folder2)

        item = await provider.validate_item("test folder 2/test folder/test.txt")

        assert item.path == "test folder 2/test folder/test.txt"
        assert item.kind == "file"
        assert item.name == "test.txt"

        await provider.validate_item("/test folder/test.txt")  # asserts not deleted

    @pytest.mark.gen_test
    async def test_intra_copy_missing(self, provider, missing_file_metadata, fs):
        fs.create_dir("test folder/")

        folder = await provider.validate_item("test folder/")

        with pytest.raises(exceptions.NotFoundError):
            await provider.intra_copy(missing_file_metadata, folder)


class TestIntraMove:
    @pytest.mark.gen_test
    async def test_intra_move_file(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_file("test.txt")

        file = await provider.validate_item("test.txt")
        folder = await provider.validate_item("test folder/")

        await provider.intra_move(file, folder)

        item = await provider.validate_item("test folder/test.txt")

        assert isinstance(item, FileSystemMetadata)
        assert item.path == "test folder/test.txt"
        assert item.kind == "file"
        assert item.name == "test.txt"

        await provider.validate_item("test folder/test.txt")

    @pytest.mark.gen_test
    async def test_intra_move_folder(self, provider, fs):
        fs.create_dir("test folder/")
        fs.create_dir("test folder 2/")
        fs.create_file("test folder/test.txt")

        folder = await provider.validate_item("test folder/")
        folder2 = await provider.validate_item("test folder 2/")

        await provider.intra_move(folder, folder2)

        item = await provider.validate_item("test folder 2/test folder/")

        assert item.path == "test folder 2/test folder/"
        assert item.kind == "folder"
        assert item.name == "test folder"

        with pytest.raises(exceptions.NotFoundError):
            await provider.validate_item("test folder/")

    @pytest.mark.gen_test
    async def test_intra_move_missing(self, provider, fs, missing_file_metadata):
        fs.create_dir("test folder/")

        folder = await provider.validate_item("test folder/")

        with pytest.raises(exceptions.NotFoundError):
            await provider.intra_move(missing_file_metadata, folder)


class TestRename:
    @pytest.mark.gen_test
    async def test_rename(self, provider, fs):
        fs.create_file("test.txt")

        item = await provider.validate_item("test.txt")

        await provider.rename(item, "new_name.txt")

        item = await provider.validate_item("new_name.txt")

        assert isinstance(item, FileSystemMetadata)
        assert item.path == "new_name.txt"
        assert item.kind == "file"
        assert item.name == "new_name.txt"

    @pytest.mark.gen_test
    async def test_rename_missing(self, provider, missing_file_metadata):
        with pytest.raises(exceptions.NotFoundError):
            await provider.rename(missing_file_metadata, "new_name")


class TestOperations:
    def test_can_intra_copy(self, provider):
        assert provider.can_intra_copy(provider)

    def test_can_intra_move(self, provider):
        assert provider.can_intra_move(provider)
