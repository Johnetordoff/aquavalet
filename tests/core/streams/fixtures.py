import pytest
import asyncio
import socket

from tornado.httputil import HTTPServerRequest
from aquavalet.core.streams.http import RequestStreamReader

@pytest.fixture
def mock_request():
    return HTTPServerRequest(uri='http://fake.com')

@pytest.fixture
async def request_stream(mock_request):
    rsock, wsock = socket.socketpair()
    reader, _ = await asyncio.open_unix_connection(sock=rsock)
    _, writer = await asyncio.open_unix_connection(sock=wsock)
    return RequestStreamReader(mock_request, reader)


