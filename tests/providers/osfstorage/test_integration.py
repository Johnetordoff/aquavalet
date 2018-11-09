import pytest
import asyncio
from aresponses import ResponsesMockServer
import aresponses
import json
import urllib.parse
from aquavalet.app import make_app

from .fixtures import (
    file_metadata_json,
    file_metadata_resp,
)

@pytest.fixture
def app():
    return make_app(False)

@pytest.mark.gen_test
async def test_metadata(http_client, base_url, file_metadata_json, file_metadata_resp):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + file_metadata_json['data']['id'])

    async with ResponsesMockServer(loop=asyncio.get_event_loop()) as server:
        server.add('api.osf.io', '/v2/files/' + file_metadata_json['data']['id'] + '/', 'GET', file_metadata_resp)

        response = await http_client.fetch(url, method='METADATA', allow_nonstandard_methods=True)

    assert response.code == 200
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/5b6ee0c390a7e0001986aff5'
    assert resp['data']['attributes']['name'] == 'test.txt'
    assert resp['data']['attributes']['kind'] == 'file'


@pytest.mark.gen_test
async def test_versions(http_client, base_url, file_metadata_json, file_metadata_resp):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + file_metadata_json['data']['id'])

    response = await http_client.fetch(url, method='METADATA', allow_nonstandard_methods=True)

    assert response.code == 200
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/5b6ee0c390a7e0001986aff5'
    assert resp['data']['attributes']['name'] == 'test.txt'
    assert resp['data']['attributes']['kind'] == 'file'
