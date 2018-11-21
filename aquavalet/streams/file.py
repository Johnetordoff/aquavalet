import os
from aquavalet.providers.filesystem.settings import CHUNK_SIZE
from aquavalet.streams.base import BaseStream

class FileStreamReader(BaseStream):

    CHUNK_SIZE=CHUNK_SIZE

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
        return self.file_pointer.tell() == self.size

    @property
    def content_range(self):
        return None

    async def _read(self, size):
        if self.read_size:
            return self.file_pointer.read(self.read_size)
        return self.file_pointer.read(size)
