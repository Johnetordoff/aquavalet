import pytest
import tornado
import json
import urllib.parse
from aquavalet.app import make_app

@pytest.fixture
def app():
    return make_app(False)

class TestMetadata:

    @pytest.mark.gen_test
    async def test_metadata(self, http_server_client, fs):
        fs.create_dir('test folder/')

        url = urllib.parse.quote('/filesystem/test folder/')
        response = yield http_server_client.fetch(url, method='METADATA', allow_nonstandard_methods=True)
        assert response.code == 200
        resp = json.loads(response.body)
        assert resp['data']['id'] == '/test folder/'
        assert resp['data']['attributes']['name'] == 'test folder'
        assert resp['data']['attributes']['kind'] == 'folder'


class TestIntraCopy:

    @pytest.mark.gen_test
    async def test_copy(self, http_server_client, fs):
        fs.create_dir('test_folder/')
        fs.create_file('test.txt')
        url = urllib.parse.quote('/filesystem/test.txt') + '?to=test_folder/&destination_provider=filesystem'
        response = await http_server_client.fetch(url, method='COPY', allow_nonstandard_methods=True)
        assert response.code == 200
        assert fs.listdir('test_folder/')[0] == 'test.txt'
        fs.reset()

class TestUpload:

    @pytest.mark.gen_test
    async def test_upload(self, http_server_client, fs):

        url = urllib.parse.quote('/filesystem/') + '?destination_provider=filesystem&new_name=test.txt'
        response = await http_server_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, body=b'test')
        assert response.code == 201

    @pytest.mark.gen_test
    async def test_upload_warn(self, http_server_client, fs):
        fs.create_file('test.txt')

        url = urllib.parse.quote('/filesystem/') + '?destination_provider=filesystem&new_name=test.txt'

        resp = await http_server_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, raise_error=False)

        assert resp.code == 409
        data = json.loads(resp.body)
        assert data['code'] == 409
        assert data['message'] == "Conflict 'test.txt'."

    @pytest.mark.gen_test
    async def test_upload_replace(self, http_server_client, fs):
        fs.create_file('test.txt', contents=b'old file')

        url = urllib.parse.quote('/filesystem/') + '?destination_provider=filesystem&new_name=test.txt&conflict=replace'
        response = await http_server_client.fetch(url, method='UPLOAD', body=b'new file', allow_nonstandard_methods=True)
        assert response.code == 201

        with open('test.txt', 'rb') as f:
            assert f.read() == b'new file'

    @pytest.mark.gen_test
    async def test_upload_rename(self, http_server_client, fs):
        fs.create_file('test.txt')
        print(fs.listdir('/'))
        url = urllib.parse.quote('/filesystem/') + '?destination_provider=filesystem&new_name=test.txt&conflict=rename'
        response = await http_server_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True)
        assert response.code == 201
        assert fs.listdir('/') == ['tmp', 'test.txt', 'test(1).txt']
        response = await http_server_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True)
        assert response.code == 201
        assert fs.listdir('/') == ['tmp', 'test.txt', 'test(1).txt', 'test(2).txt']
