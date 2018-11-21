import uuid
import asyncio

from aquavalet.streams.base import BaseStream, MultiStream, StringStream


class ResponseStreamReader(BaseStream):

    def __init__(self, response, size=None, name=None):
        super().__init__()
        if 'Content-Length' in response.headers:
            self._size = int(response.headers['Content-Length'])
        else:
            self._size = size
        self._name = name
        self.response = response
        self.iter_any = response.content.iter_any

    @property
    def partial(self):
        return self.response.status == 206

    @property
    def content_type(self):
        return self.response.headers.get('Content-Type', 'application/octet-stream')

    @property
    def content_range(self):
        return self.size

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    async def _read(self, size):
        chunk = await self.response.content.read(size)

        if not chunk:
            self.feed_eof()
            await self.response.release()

        return chunk


class RequestStreamReader(BaseStream):

    def __init__(self, request, reader):
        super().__init__()
        self.reader = reader
        self.request = request

    @property
    def size(self):
        return int(self.request.headers.get('Content-Length'))

    def at_eof(self):
        return self.reader.at_eof()

    async def _read(self, size):
        if self.reader.at_eof():
            return b''
        if size < 0:
            return (await self.reader.read(size))
        try:
            return (await self.reader.readexactly(size))
        except asyncio.IncompleteReadError as e:
            return e.partial
