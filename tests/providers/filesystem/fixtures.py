import os
import pytest
import shutil
from aquavalet.providers.filesystem import FileSystemProvider
from aquavalet.providers.filesystem.metadata import FileSystemMetadata

@pytest.fixture
def provider():
    return FileSystemProvider({})

@pytest.fixture
def file_metadata():
    return FileSystemMetadata(path='test folder/flower.jpg')

@pytest.fixture
def folder_metadata():
    return FileSystemMetadata(path='test folder/other_subfolder/')


