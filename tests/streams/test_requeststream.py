import pytest
from tests.streams.fixtures import request_stream


class TestRequestStream:

    @pytest.mark.asyncio
    async def test_request_stream_read(self, request_stream):
        assert await request_stream.read() == b'test data'
        assert request_stream.at_eof()

    @pytest.mark.asyncio
    async def test_request_stream_read_exact(self, request_stream):
        assert await request_stream.read(4) == b'test'
        assert not request_stream.at_eof()

    @pytest.mark.asyncio
    async def test_request_stream_size(self, request_stream):
        assert request_stream.size == 9
