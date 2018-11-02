import pytest
import asyncio
import aiohttp
import socket


from aquavalet.core.streams.http import RequestStreamReader
from aquavalet.core.streams.file import FileStreamReader
from aquavalet.core.streams.zip import ZipStreamReader
from aquavalet.core.utils import ZipStreamGeneratorReader
from tests.providers.filesystem.fixtures import provider


from tornado.httputil import HTTPServerRequest

@pytest.fixture()
def request_stream(stream_data=b'test data'):
    reader = asyncio.StreamReader()
    reader.feed_data(stream_data)
    reader.feed_eof()

    headers = {'Content-Length': len(stream_data)}
    request = HTTPServerRequest(uri='http://fake.com', headers=headers, body=stream_data)
    return RequestStreamReader(request, reader)


class RequestStreamFactory(object):

    def __new__(self):
        return request_stream()

@pytest.fixture()
async def response_stream(stream_data=b'test data'):
    pass

@pytest.fixture()
async def file_stream(fs, range=None):
    fs.create_file('test.txt', contents=b'test')
    fp = open('test.txt')
    return FileStreamReader(fp, range=range)


@pytest.fixture()
async def zip_generator(fs, provider):
    fs.create_dir('test folder/')
    fs.create_dir('test folder/test folder 2/')
    fs.create_file('test folder/test-1.txt', contents=b'test-1')
    fs.create_file('test folder/test-2.txt', contents=b'test-2')
    fs.create_file('test folder/test folder 2/test-3.txt', contents=b'test-3')

    session = aiohttp.ClientSession()
    item = await provider.validate_item('/')
    children = await provider.children(item)
    return ZipStreamGeneratorReader(provider, item, children, session)


@pytest.fixture()
async def zip_stream(fs, zip_generator):
    return ZipStreamReader(zip_generator)


