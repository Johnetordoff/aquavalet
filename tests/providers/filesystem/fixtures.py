import os
import pytest
import shutil
from aquavalet.providers.filesystem import FileSystemProvider
from aquavalet.providers.filesystem.metadata import FileSystemMetadata

@pytest.fixture
def provider():
    return FileSystemProvider({})

@pytest.fixture
def missing_file_metadata():
    item = FileSystemMetadata(path='test folder/flower.jpg')
    item.raw['path'] = '/missing.txt'
    return item

@pytest.fixture
def root_metadata():
    return FileSystemMetadata.root()

@pytest.fixture
def file_metadata():
    return FileSystemMetadata(path='test folder/flower.jpg')

@pytest.fixture
def folder_metadata():
    return FileSystemMetadata(path='test folder/other_subfolder/')


