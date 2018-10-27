import pytest
from tests.streams.fixtures import zip_generator
from tests.providers.filesystem.fixtures import provider
from aquavalet.core.utils import ZipStreamGeneratorReader

class TestZipStreamGeneratorReader:

    @pytest.mark.asyncio
    async def test_zip_generator(self, zip_generator):
        filename, stream = await zip_generator.__anext__()
        assert filename == 'tmp'
        assert await stream.read() == b''

        filename, stream = await zip_generator.__anext__()
        assert filename == 'test folder/test-1.txt'
        assert await stream.read() == b'test-1'

class TestZipStreamReader:

    @pytest.mark.asyncio
    async def test_zip_stream_read(self, request_stream):
        assert await request_stream.read() == b'test data'
        assert request_stream.at_eof()

    @pytest.mark.asyncio
    async def test_request_stream_size(self, request_stream):
        assert request_stream.size == 9


class TestZipStreamReader:
    pass



