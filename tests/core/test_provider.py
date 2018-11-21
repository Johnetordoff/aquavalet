import pytest

from tests import utils
from unittest import mock
from aquavalet import metadata, exceptions
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

def test_build_range_header(self, provider1):
    assert 'bytes=0-' == provider1._build_range_header((0, None))
    assert 'bytes=10-' == provider1._build_range_header((10, None))
    assert 'bytes=10-100' == provider1._build_range_header((10, 100))
    assert 'bytes=-255' == provider1._build_range_header((None, 255))
