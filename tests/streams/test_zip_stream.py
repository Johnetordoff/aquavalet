import io
import pytest
import zipfile

from tests.streams.fixtures import zip_generator, zip_stream
from tests.providers.filesystem.fixtures import provider
from aquavalet.core.utils import ZipStreamGeneratorReader


class TestZipStreamGeneratorReader:

    @pytest.mark.asyncio
    async def test_zip_generator(self, zip_generator):
        filename, stream = await zip_generator.__anext__()
        assert filename == 'tmp/'
        assert await stream.read() == b''

        filename, stream = await zip_generator.__anext__()
        assert filename == 'test folder/test-1.txt'
        assert await stream.read() == b'test-1'

        filename, stream = await zip_generator.__anext__()
        assert filename == 'test folder/test-2.txt'
        assert await stream.read() == b'test-2'

        filename, stream = await zip_generator.__anext__()
        assert filename == 'test folder/test folder 2/test-3.txt'
        assert await stream.read() == b'test-3'

        with pytest.raises(StopAsyncIteration):
            await zip_generator.__anext__()

        await zip_generator.session.close()


class TestZipStreamReader:

    @pytest.mark.asyncio
    async def test_zip_stream_read(self, zip_stream):
        data = await zip_stream.read()
        zf = zipfile.ZipFile(io.BytesIO(data), "r")
        files = zf.infolist()
        assert files[0].filename == 'tmp/'
        assert files[1].filename == 'test folder/test-1.txt'
        assert files[2].filename == 'test folder/test-2.txt'
        assert files[3].filename == 'test folder/test folder 2/test-3.txt'

    @pytest.mark.asyncio
    async def test_zip_stream_read_partial(self, zip_stream):
        data = await zip_stream.read(10)  # No idea why you'd want to do this!
        assert len(data) == 10


