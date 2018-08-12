from http import HTTPStatus

import pytest

from aquavalet.core.streams.http import ResponseStreamReader


@pytest.fixture
def mock_content_eof():
    return type('mock_content_eof', (object,), {'read': MockCoroutine(return_value=None)})


class MockResponse:
    status = HTTPStatus.OK
    headers = {'Content-Length': 100, 'Content-Range': '0-100'}
    content = mock_content()
    release = MockCoroutine()


class MockResponseNoContentLength:
    status = HTTPStatus.OK
    headers = {'Content-Range': '0-0'}
    content = mock_content()
    release = MockCoroutine()


class MockResponseNoContent:
    status = HTTPStatus.OK
    headers = {'Content-Range': '0-0'}
    content = mock_content_eof()
    release = MockCoroutine()


@pytest.fixture
def mock_response_stream_reader():
    return ResponseStreamReader(MockResponse(), size=None, name='test stream')


@pytest.fixture
def mock_response_stream_reader_no_size():
    return ResponseStreamReader(MockResponseNoContentLength(), size=None, name='test stream')


@pytest.fixture
def mock_response_stream_reader_no_content():
    return ResponseStreamReader(MockResponseNoContent(), size=None, name='test stream')
