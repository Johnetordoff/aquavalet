import pytest
import json
import aresponses
import urllib.parse
from aquavalet.server.app import make_app
from tests.providers.osfstorage.fixtures import file_metadata_resp

@pytest.fixture
def app():
    return make_app(False)

@pytest.mark.gen_test
def test_metadata(http_client, base_url):
    response = yield http_client.fetch(base_url + urllib.parse.quote('/filesystem/code/test folder/')+ '?serve=meta')
    assert response.code == 200
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/code/test folder/'
    assert resp['data']['attributes']['name'] == 'test folder'


@pytest.mark.gen_test
def test_copy(http_client, base_url):
    #aresponses.add('files.osf.io', '/v1/resources/vy6x2/providers/osfstorage/', 'put', file_metadata_resp)

    response = yield http_client.fetch(base_url + urllib.parse.quote('/filesystem/code/test folder/flower.jpg') + '?serve=copy&to=/osfstorage/vy6x2/&destination_provider=osfstorage&conflict=replace')
    assert response.code == 200
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/code/test folder/'
    assert resp['data']['attributes']['name'] == 'test folder'

@pytest.mark.gen_test
def test_replace(http_client, base_url):
    #aresponses.add('files.osf.io', '/v1/resources/vy6x2/providers/osfstorage/', 'put', file_metadata_resp)
    # resp = requests.request('UPLOAD', url='http://localhost:7777/osfstorage/osfstorage/vy6x2/', params={'new_name': 'new file'}, data=data)
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/vy6x2/') + '?serve=upload&to=/osfstorage/vy6x2/&destination_provider=osfstorage&conflict=replace&new_name=test.txt'
    response = yield http_client.fetch(url, json=b'1234')
    assert response.code == 200
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/code/test folder/'
    assert resp['data']['attributes']['name'] == 'test folder'
