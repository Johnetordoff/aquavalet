import os
import asyncio
import json
import aresponses

from tests.utils import json_resp, data_resp, empty_resp

import pytest

from aquavalet.providers.osfstorage.provider import OSFStorageProvider
from aquavalet.providers.osfstorage.metadata import OsfMetadata
from aquavalet.app import make_app

def from_fixture_json(key):
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)[key]


@pytest.fixture
def app():
    return make_app(False)


@pytest.fixture
def upload_resp():
    data = from_fixture_json('upload_response')
    return json_resp(data)


@pytest.fixture
def create_folder_response_json():
    return from_fixture_json('create_folder_response')


@pytest.fixture
def create_folder_resp(create_folder_response_json):
    return json_resp(create_folder_response_json, status=201)


@pytest.fixture
def delete_resp():
    return empty_resp(status=204)


@pytest.fixture
def folder_metadata_json():
    return from_fixture_json('folder_metadata')


@pytest.fixture
def folder_metadata_resp(folder_metadata_json):
    return json_resp(folder_metadata_json)


@pytest.fixture
def download_resp():
    return data_resp(b'test stream!')


@pytest.fixture
def file_metadata_json():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)['file_metadata']


@pytest.fixture
def version_metadata_json():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)['versions_metadata']


@pytest.fixture
def file_metadata_resp(file_metadata_json):
    return json_resp(file_metadata_json)


@pytest.fixture
def version_metadata_resp(version_metadata_json):
    return json_resp(version_metadata_json)


class FileMetadataRespFactory:
    def __new__(self):
        return file_metadata_resp(file_metadata_json())


@pytest.fixture
def response_404_json():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)['api_response_404']


@pytest.fixture
def response_404(response_404_json):
    return json_resp(response_404_json, status=404)


@pytest.fixture
def children_resp():
    data = from_fixture_json('children_response')
    return json_resp(data)


@pytest.fixture
def file_metadata_object(file_metadata_json, provider):
    return OsfMetadata(file_metadata_json['data']['attributes'], provider.internal_provider, provider.resource)


@pytest.fixture
def folder_metadata_object(folder_metadata_json, provider):
    return OsfMetadata(folder_metadata_json['data']['attributes'], provider.internal_provider, provider.resource)


@pytest.fixture
def revision_metadata_object(revisions_metadata):
    return OsfMetadata(revisions_metadata['revisions'][0])


@pytest.fixture
def provider():
    provider = OSFStorageProvider({})
    provider.internal_provider = 'osfstorage'
    provider.resource = 'guid0'
    return provider


@pytest.fixture
async def mock_file_metadata(aresponses, file_metadata_json):
    headers = {'content-type': 'application/json'}
    resp = aresponses.Response(body=json.dumps(file_metadata_json), headers=headers, status=200)
    aresponses.add('api.osf.io', '/v2/files/' + file_metadata_json['data']['id'], 'GET', resp)


@pytest.fixture
async def mock_file_metadata2(file_metadata_json):
    server = aresponses.ResponsesMockServer(loop=asyncio.get_event_loop())
    await server.__aenter__()
    headers = {'content-type': 'application/json'}
    resp = aresponses.Response(body=json.dumps(file_metadata_json), headers=headers, status=200)
    server.add('api.osf.io', '/v2/files/' + file_metadata_json['data']['id'] + '/', 'GET', resp)


@pytest.fixture
async def mock_file_download(aresponses, file_metadata_json, download_resp):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'GET', download_resp)


@pytest.fixture
async def mock_file_upload(aresponses, file_metadata_json, upload_resp):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'PUT', upload_resp)


@pytest.fixture
async def mock_file_missing(aresponses, file_metadata_json, response_404):
    aresponses.add('api.osf.io', response=response_404)


@pytest.fixture
async def mock_file_delete(aresponses, file_metadata_json, delete_resp):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'DELETE', delete_resp)


@pytest.fixture
async def mock_create_folder(aresponses, file_metadata_json, create_folder_resp):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'PUT', create_folder_resp)


@pytest.fixture
async def mock_rename(aresponses, file_metadata_json, file_metadata_resp):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'POST', file_metadata_resp)


@pytest.fixture
async def mock_children(aresponses, folder_metadata_json, children_resp):
    path = '/v1/resources/guid0/providers/osfstorage/' + folder_metadata_json['data']['id'] + '/'
    aresponses.add('files.osf.io', path, 'GET', children_resp)

@pytest.fixture
async def mock_intra_copy(aresponses, file_metadata_json, children_resp):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'POST', file_metadata_resp)

