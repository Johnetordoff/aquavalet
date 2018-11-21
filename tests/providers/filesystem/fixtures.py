import pytest
from aquavalet.providers.filesystem import FileSystemProvider
from aquavalet.providers.filesystem.metadata import FileSystemMetadata
import linecache
import tokenize

import py
import pytest

from pyfakefs.fake_filesystem_unittest import Patcher


@pytest.fixture
def provider():
    return FileSystemProvider({})


@pytest.fixture
def missing_file_metadata(fs):
    fs.create_file('test.txt')
    item = FileSystemMetadata(path='test.txt')
    item.raw['path'] = '/missing.txt'
    return item
