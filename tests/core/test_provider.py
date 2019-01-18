import pytest
import abc

from aquavalet.provider import BaseProvider

@pytest.fixture
def provider1():
    return BaseProvider('fake auth')


@pytest.fixture
def provider2():
    return BaseProvider('fake auth 2')


class TestBaseProvider:

    def test_eq(self, provider1, provider2):
        assert provider1 == provider1
        assert provider2 == provider2
        assert provider1 != provider2

    def test_serialize(self, provider1):
        assert provider1.serialized() == {
            'name': 'base provider',
            'auth': 'fake auth'
        }


def test_build_range_header(provider1):
    assert 'bytes=0-' == provider1._build_range_header((0, None))
    assert 'bytes=10-' == provider1._build_range_header((10, None))
    assert 'bytes=10-100' == provider1._build_range_header((10, 100))
    assert 'bytes=-255' == provider1._build_range_header((None, 255))


from tests.providers.osfstorage.utils import MockOsfstorageServer



class BaseProviderTestSuite(metaclass=abc.ABCMeta):

    @classmethod
    @abc.abstractmethod
    async def test_validate_item(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_download(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_download_version(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_download_range(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_download_zip(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_upload(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_delete(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_metadata(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_create_folder(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_rename(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_children(self, server, provider):
        raise NotImplementedError()

    @abc.abstractmethod
    async def test_versions(self, server, provider):
        raise NotImplementedError()
