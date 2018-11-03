import pytest
from tests.streams.fixtures import file_stream

class TestFileStream:

    @pytest.mark.asyncio
    async def test_file_stream_read(self, file_stream):
        assert await file_stream.read() == 'test'
        assert file_stream.at_eof()

    @pytest.mark.asyncio
    async def test_file_stream_read_exact(self, file_stream):
        assert await file_stream.read(2) == 'te'
        assert not file_stream.at_eof()

    @pytest.mark.asyncio
    async def test_file_stream_read_range_end(self, fs):
        file_stream_range = await file_stream(fs, range=(2,5))
        assert await file_stream_range.read() == 'st'
        assert file_stream_range.at_eof()

    @pytest.mark.asyncio
    async def test_file_stream_read_range_beginning(self, fs):
        file_stream_range = await file_stream(fs, range=(0,1))
        assert await file_stream_range.read() == 'te'
        assert file_stream_range.at_eof()  # Not sure if correct

    @pytest.mark.asyncio
    async def test_file_stream_read_chunk(self, fs):

        file_stream_range = await file_stream(fs)
        file_stream_range.CHUNK_SIZE = 1
        ind = 0
        test_data = 'test'
        async for chunk in file_stream_range:
            assert chunk == test_data[ind]
            ind += 1

        assert file_stream_range.at_eof()  # Not sure if correct

    @pytest.mark.asyncio
    async def test_file_stream_size(self, file_stream):
        assert file_stream.size == 4
