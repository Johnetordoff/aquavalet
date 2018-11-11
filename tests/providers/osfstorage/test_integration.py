import pytest
import asyncio
from aresponses import ResponsesMockServer
import aresponses
import json
import urllib.parse

import tornado

from .fixtures import (
    app,
    file_metadata_json,
    file_metadata_resp,
    download_resp,
    FileMetadataRespFactory,
    version_metadata_resp,
    version_metadata_json
)


@pytest.mark.gen_test
async def test_metadata(http_client, base_url, file_metadata_json, file_metadata_resp):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + file_metadata_json['data']['id'])

    async with ResponsesMockServer(loop=asyncio.get_event_loop()) as server:
        server.add('api.osf.io', '/v2/files/' + file_metadata_json['data']['id'], 'GET', file_metadata_resp)

        response = await http_client.fetch(url, method='METADATA', allow_nonstandard_methods=True)

    assert response.code == 200
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/5b6ee0c390a7e0001986aff5'
    assert resp['data']['attributes']['name'] == 'test.txt'
    assert resp['data']['attributes']['kind'] == 'file'


@pytest.mark.gen_test
async def test_download(http_client, base_url, file_metadata_json, download_resp, file_metadata_resp):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + file_metadata_json['data']['id'])

    async with ResponsesMockServer(loop=asyncio.get_event_loop()) as server:
        server.add('api.osf.io', '/v2/files/' + file_metadata_json['data']['id'], 'GET', file_metadata_resp)
        server.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id'], 'GET', download_resp)

        response = await http_client.fetch(url, method='DOWNLOAD', allow_nonstandard_methods=True)

    assert response.code == 200
    assert response.body == b'test stream!'


@pytest.mark.gen_test
async def test_intra_copy(http_client, base_url, file_metadata_json, file_metadata_resp, download_resp):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + file_metadata_json['data']['id']) + '?to=/osfstorage/guid0/&destination_provider=osfstorage'

    async with ResponsesMockServer(loop=asyncio.get_event_loop()) as server:
        server.add('api.osf.io', '/v2/files/' + file_metadata_json['data']['id'], 'GET', file_metadata_resp)
        server.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id'], 'POST', file_metadata_resp)

        response = await http_client.fetch(url, method='COPY', allow_nonstandard_methods=True)

    assert response.code == 200
    assert response.body == b'test stream!'


@pytest.mark.gen_test
async def test_versions(http_client, base_url, file_metadata_json, version_metadata_resp, file_metadata_resp, version_metadata_json):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + file_metadata_json['data']['id'])
    async with ResponsesMockServer(loop=asyncio.get_event_loop()) as server:
        server.add('api.osf.io', '/v2/files/' + file_metadata_json['data']['id'], 'GET', file_metadata_resp)
        server.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id'], 'GET', version_metadata_resp)
        response = await http_client.fetch(url, method='VERSIONS', allow_nonstandard_methods=True)

    assert response.code == 200
    resp = json.loads(response.body)
    print(resp)
    assert resp['data'][0]['attributes']['version_id'] == '2'
    assert resp['data'][1]['attributes']['version_id'] == '1'
    assert resp['data'][0]['version_id'] == '/5b6ee0c390a7e0001986aff5'
    assert resp['data']['attributes']['name'] == 'test.txt'
    assert resp['data']['attributes']['kind'] == 'file'


@pytest.mark.gen_test
async def test_upload_new_version(http_client, base_url):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/') + '?new_name=test&conflict=new_version'
    print(url)
    response = await http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, body=b'12345')

    assert response.code == 201
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/5b6ee0c390a7e0001986aff5'
    assert resp['data']['attributes']['name'] == 'test.txt'
    assert resp['data']['attributes']['kind'] == 'file'


@pytest.mark.gen_test
async def test_upload_warn(http_client, base_url):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/') + '?new_name=test&conflict=warn'
    print(url)
    'http://0.0.0.0:7777/osfstorage/osfstorage/km7z4/5bcb4bc3a334dd0016f221b0/?serve=copy&destination_provider=osfstorage&to=/osfstorage/km7z4/5bb38210af0e400016ef47bb/'

    with pytest.raises(tornado.httpclient.HTTPError):
        response = await http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, body=b'12345')

    assert response.code == 409
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/5b6ee0c390a7e0001986aff5'
    assert resp['data']['attributes']['name'] == 'test.txt'
    assert resp['data']['attributes']['kind'] == 'file'
