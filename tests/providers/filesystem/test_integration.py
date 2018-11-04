import pytest
import tornado
import json
import urllib.parse
from aquavalet.app import make_app

@pytest.fixture
def app():
    return make_app(False)

@pytest.mark.gen_test
def test_metadata(http_client, base_url, fs):
    fs.create_dir('test folder/')

    url = base_url + urllib.parse.quote('/filesystem/test folder/')
    response = yield http_client.fetch(url, method='METADATA', allow_nonstandard_methods=True)
    assert response.code == 200
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/test folder/'
    assert resp['data']['attributes']['name'] == 'test folder'
    assert resp['data']['attributes']['kind'] == 'folder'


@pytest.mark.gen_test
def test_copy(http_client, base_url, fs):
    fs.create_dir('test_folder/')
    fs.create_file('test.txt')
    url = base_url + urllib.parse.quote('/filesystem/test.txt') + '?to=test_folder/&destination_provider=filesystem'
    response = yield http_client.fetch(url, method='COPY', allow_nonstandard_methods=True)
    assert response.code == 200
    assert fs.listdir('test_folder/')[0] == 'test.txt'


@pytest.mark.gen_test
def test_upload(http_client, base_url, fs):

    url = base_url + urllib.parse.quote('/filesystem/') + '?destination_provider=filesystem&new_name=test.txt'

    response = yield http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True)
    assert response.code == 201


@pytest.mark.gen_test
def test_upload_warn(http_client, base_url, fs):
    fs.create_dir('test_folder/')
    fs.create_file('test_folder/test.txt')

    url = base_url + urllib.parse.quote('/filesystem/test_folder/') + '?destination_provider=filesystem&new_name=test.txt'

    with pytest.raises(tornado.httpclient.HTTPError) as exc:
        yield http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True)

    assert exc.value.code == 409
    assert exc.value.message == 'Conflict'


@pytest.mark.gen_test
def test_upload_replace(http_client, base_url, fs):
    fs.create_dir('test_folder/')
    fs.create_file('test_folder/test.txt', contents=b'old file')

    url = base_url + urllib.parse.quote('/filesystem/test_folder/') + '?destination_provider=filesystem&new_name=test.txt&conflict=replace'
    response = yield http_client.fetch(url, method='UPLOAD', body=b'new file', allow_nonstandard_methods=True)
    assert response.code == 200

    with open('test_folder/test.txt', 'rb') as f:
         assert f.read() == b'new file'


@pytest.mark.gen_test
def test_upload_rename(http_client, base_url, fs):
    fs.create_dir('test_folder/')
    fs.create_file('test_folder/test.txt')

    url = base_url + urllib.parse.quote('/filesystem/test_folder/') + '?destination_provider=filesystem&new_name=test.txt&conflict=rename'
    response = yield http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True)
    assert response.code == 201
    assert fs.listdir('test_folder/') == ['test.txt', 'test(1).txt']
    response = yield http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True)
    assert response.code == 201
    assert fs.listdir('test_folder/') == ['test.txt', 'test(1).txt', 'test(2).txt']
