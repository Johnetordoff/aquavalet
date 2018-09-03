import pytest
import json
import aresponses
import urllib.parse
from aquavalet.server.app import make_app

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
def test_copy(http_client, aresponses, base_url):
    aresponses.add('api.osf.io', '/v2/files/5b6ee0c390a7e0001986aff5/', 'get', file_metadata_resp)
    response = yield http_client.fetch(base_url + urllib.parse.quote('/filesystem/code/test folder/flower.jpg') + '?serve=copy&to=/osfstorage/vy6x2/&destination_provider=osfstorage')
    assert response.code == 200
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/code/test folder/'
    assert resp['data']['attributes']['name'] == 'test folder'
