import pytest
import asyncio
from aresponses import ResponsesMockServer
import aresponses
import json
import urllib.parse

import tornado

from .utils import MockOsfstorageServer

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

    async with MockOsfstorageServer() as server:
        server.mock_api_get(file_metadata_json)
        response = await http_client.fetch(url, method='METADATA', allow_nonstandard_methods=True)

    assert response.code == 200
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/5b6ee0c390a7e0001986aff5'
    assert resp['data']['attributes']['name'] == 'test.txt'
    assert resp['data']['attributes']['kind'] == 'file'


@pytest.mark.gen_test
async def test_download(http_client, base_url, file_metadata_json):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + file_metadata_json['data']['id'])

    async with MockOsfstorageServer() as server:
        server.mock_download(file_metadata_json, b'test stream!')

        response = await http_client.fetch(url, method='DOWNLOAD', allow_nonstandard_methods=True)

    assert response.code == 200
    assert response.body == b'test stream!'


@pytest.mark.gen_test
async def test_intra_copy(http_client, base_url, file_metadata_json):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + file_metadata_json['data']['id']) + '?to=/osfstorage/guid0/&destination_provider=osfstorage'
    file_resp = FileMetadataRespFactory()

    async with MockOsfstorageServer() as server:
        server.mock_api_get(file_metadata_json)
        server.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id'], 'POST', file_resp)

        response = await http_client.fetch(url, method='COPY', allow_nonstandard_methods=True)

    assert response.code == 200


@pytest.mark.gen_test
async def test_versions(http_client, base_url, file_metadata_json, version_metadata_resp, file_metadata_resp, version_metadata_json):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + file_metadata_json['data']['id'])
    async with MockOsfstorageServer() as server:
        server.mock_api_get(file_metadata_json)
        server.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id'], 'GET', version_metadata_resp)
        response = await http_client.fetch(url, method='VERSIONS', allow_nonstandard_methods=True)

    assert response.code == 200
    resp = json.loads(response.body)
    assert resp['data'][0]['attributes']['version_id'] == '2'
    assert resp['data'][1]['attributes']['version_id'] == '1'


@pytest.mark.gen_test
async def test_upload_new_version(http_client, base_url):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/') + '?new_name=test&conflict=new_version'
    response = await http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, body=b'12345')

    assert response.code == 201
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/5b6ee0c390a7e0001986aff5'
    assert resp['data']['attributes']['name'] == 'test.txt'
    assert resp['data']['attributes']['kind'] == 'file'


@pytest.mark.gen_test
async def test_upload_warn(http_client, base_url):
    url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/') + '?new_name=test&conflict=warn'
    with pytest.raises(tornado.httpclient.HTTPError):
        async with MockOsfstorageServer() as server:
            response = await http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, body=b'12345')

    assert response.code == 409
    resp = json.loads(response.body)
    assert resp['data']['id'] == '/5b6ee0c390a7e0001986aff5'
    assert resp['data']['attributes']['name'] == 'test.txt'
    assert resp['data']['attributes']['kind'] == 'file'
