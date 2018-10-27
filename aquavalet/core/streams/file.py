import os
import asyncio
import aiofiles
import mimetypes

from aquavalet.core.streams.base import BaseStream

class FileStreamReader(BaseStream):

    def __init__(self, file_pointer, range=None):
        super().__init__()
        self.file_pointer = file_pointer
        self.read_size = None
        self.file_gen = None
        self.content_type = 'application/octet-stream'

        if range:
            self.file_pointer.seek(range[0])
            self.read_size = range[1] - range[0] + 1
            self.partial = True
        else:
            self.partial = False

    @property
    def size(self):
        if self.read_size:
            return self.read_size
        else:
            cursor = self.file_pointer.tell()
            self.file_pointer.seek(0, os.SEEK_END)
            ret = self.file_pointer.tell()
            self.file_pointer.seek(cursor)
            return ret

    def close(self):
        self.file_pointer.close()
        self.feed_eof()

    def at_eof(self):
        print(self.file_pointer.tell())
        print(self.size)

        return self.file_pointer.tell() == self.size


    @property
    def content_range(self):
        return None

    async def _read(self, size):
        if self.read_size:
            return self.file_pointer.read(self.read_size)
        return self.file_pointer.read(size)


class ChunkedFileGenerator():

    def __init__(self, stream_read):
        self.stream_read = stream_read

    async def __aiter__(self):
        return self

    async def __anext__(self):
        chunk = self.stream_read.file_pointer.read(self.stream_read.read_size)
        if not chunk:
            raise StopAsyncIteration()

        return chunk
