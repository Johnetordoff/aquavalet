import pytest
import hashlib

from tests import utils


class FileMetadata:

    def test_file(self, provider, file):

        assert file.provider == provider.name
        assert isinstance(file, provider.Item)

        assert file.is_file is True
        assert file.is_folder is False
        assert file.is_root is False
        assert file.kind == 'file'
        assert file.name == 'test.txt'
        assert file.mimetype == 'text/plain'
        assert file.unix_path == '/test.txt'

    def test_folder(self, provider, folder):

        assert folder.provider == provider.name
        assert isinstance(folder, provider.Item)

        assert folder.is_file is False
        assert folder.is_folder is True
        assert folder.is_root is False
        assert folder.kind == 'folder'
        assert folder.name == 'test_folder'
        assert folder.mimetype is None
        assert folder.unix_path == '/test_folder/'

    def test_root(self, provider, root):

        assert root.is_file is False
        assert root.is_folder is True
        assert root.is_root is True
        assert root.kind == 'folder'
        assert root.name == 'osfstorage root'
        assert root.mimetype is None
        assert root.unix_path == '/'

    def test_version(self, provider, versions):

        for ind, file in enumerate(versions):
            assert file.provider == provider.name
            assert isinstance(file, provider.Item)

            assert file.is_file is True
            assert file.is_folder is False
            assert file.is_root is False
            assert file.kind == 'file'
            assert file.name == 'test.txt'
            assert file.mimetype == 'text/plain'
            assert file.unix_path == '/test.txt'
            assert file.version_id == str(len(versions) - ind)
