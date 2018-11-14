import pytest

from tests.core.test_metadata import FileMetadata
from tests.providers.osfstorage.fixtures import (
    provider,
    folder_metadata_object,
    file_metadata_object,
    version_metadata_object,
    root_metadata_object
)


class TestOsfFileMetadata(FileMetadata):

    @pytest.fixture
    def provider(self, provider):
        return provider

    @pytest.fixture
    def file(self, file_metadata_object):
        return file_metadata_object

    @pytest.fixture
    def versions(self, version_metadata_object):
        return version_metadata_object

    @pytest.fixture
    def folder(self, folder_metadata_object):
        return folder_metadata_object

    @pytest.fixture
    def root(self, root_metadata_object):
        return root_metadata_object
