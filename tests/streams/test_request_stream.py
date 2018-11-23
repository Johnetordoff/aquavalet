import pytest
from tests.streams.fixtures import RequestStreamFactory

class TestRequestStream:

    @pytest.mark.asyncio
    async def test_request_stream_read(self):
        stream = RequestStreamFactory()
        assert await stream.read() == b'test data'
        assert stream.at_eof()

    @pytest.mark.asyncio
    async def test_request_stream_read_exact(self):
        stream = RequestStreamFactory()

        assert await stream.read(4) == b'test'
        assert not stream.at_eof()

    @pytest.mark.asyncio
    async def test_request_stream_read_chunked(self):
        stream = RequestStreamFactory()

        ind = 0
        test_data = 'test data'
        stream.CHUNK_SIZE = 1
        async for chunk in stream:
            assert chunk == bytes(test_data[ind], 'utf-8')
            ind += 1

        assert stream.at_eof()

    @pytest.mark.asyncio
    async def test_request_stream_size(self):
        stream = RequestStreamFactory()

        assert stream.size == 9
