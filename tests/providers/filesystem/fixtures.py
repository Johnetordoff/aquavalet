import os
import pytest
import shutil
from aquavalet.providers.filesystem import FileSystemProvider

@pytest.fixture
def provider():
    return FileSystemProvider({})


@pytest.fixture(scope="function", autouse=True)
def setup_filesystem(provider):
    shutil.rmtree('test folder')
    os.makedirs('test folder', exist_ok=True)

    with open(os.path.join('test folder', 'flower.jpg'), 'wb') as fp:
        fp.write(b'I am a file')

    os.mkdir(os.path.join('test folder', 'subfolder'))
    os.mkdir(os.path.join('test folder', 'other_subfolder'))

    with open(os.path.join('test folder', 'subfolder', 'nested.txt'), 'wb') as fp:
        fp.write(b'Here is my content')


