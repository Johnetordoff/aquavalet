import pytest
import asyncio
import socket


from aquavalet.core.streams.http import RequestStreamReader
from aquavalet.core.streams.file import FileStreamReader
from tornado.httputil import HTTPServerRequest

@pytest.fixture()
async def request_stream(stream_data=b'test data'):
    reader = asyncio.StreamReader()
    reader.feed_data(stream_data)
    reader.feed_eof()

    headers = {'Content-Length': len(stream_data)}
    request = HTTPServerRequest(uri='http://fake.com', headers=headers, body=stream_data)
    return RequestStreamReader(request, reader)


@pytest.fixture()
async def file_stream(fs, fp=None, range=None):
    fs.create_file('test.txt', contents=b'test')
    fp = open('test.txt')
    return FileStreamReader(fp, range=range)


