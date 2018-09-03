import os
import pytest
import shutil
from aquavalet.providers.filesystem import FileSystemProvider
from aquavalet.providers.filesystem.metadata import FileSystemMetadata

@pytest.fixture
def provider():
    return FileSystemProvider({})

@pytest.fixture(scope="function", autouse=True)
def setup_filesystem(provider):
    try:
        shutil.rmtree('test folder')
    except:
        pass
    os.makedirs('test folder', exist_ok=True)

    with open(os.path.join('test folder', 'flower.jpg'), 'wb') as fp:
        fp.write(b'I am a file')

    os.mkdir(os.path.join('test folder', 'subfolder'))
    os.mkdir(os.path.join('test folder', 'other_subfolder'))

    with open(os.path.join('test folder', 'subfolder', 'nested.txt'), 'wb') as fp:
        fp.write(b'Here is my content')



@pytest.fixture
def missing_file_metadata(setup_filesystem):
    item = FileSystemMetadata(path='test folder/flower.jpg')
    item.raw['path'] = '/missing.txt'
    return item

@pytest.fixture
def root_metadata(setup_filesystem):
    return FileSystemMetadata.root()

@pytest.fixture
def file_metadata(setup_filesystem):
    return FileSystemMetadata(path='test folder/flower.jpg')

@pytest.fixture
def folder_metadata(setup_filesystem):
    return FileSystemMetadata(path='test folder/other_subfolder/')


