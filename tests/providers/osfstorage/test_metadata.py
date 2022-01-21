import pytest

from tests.core.test_metadata import FileMetadataTests
from tests.providers.osfstorage.fixtures import provider, root_metadata_object

from tests.providers.osfstorage.utils import MockOsfstorageServer


class TestOsfFileMetadata(FileMetadataTests):
    @pytest.fixture
    def provider(self, provider):
        return provider

    @pytest.fixture
    def file(self):
        return MockOsfstorageServer().get_file_item()

    @pytest.fixture
    def versions(self):
        return MockOsfstorageServer().get_version_item()

    @pytest.fixture
    def folder(self):
        return MockOsfstorageServer().get_folder_item()

    @pytest.fixture
    def root(self, root_metadata_object):
        return root_metadata_object
