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


def upload_resp():
    data = from_fixture_json('upload_metadata')
    return json_resp(data)


@pytest.fixture
def create_folder_response_json():
    return from_fixture_json('create_folder_metadata')


def create_folder_resp():
    return json_resp(from_fixture_json('create_folder_metadata'), status=201)


@pytest.fixture
def delete_resp():
    return empty_resp(status=204)


def get_folder_metadata_json():
    return from_fixture_json('folder_metadata')


@pytest.fixture
def folder_metadata_resp(folder_metadata_json):
    return json_resp(folder_metadata_json)


@pytest.fixture
def download_resp():
    return data_resp(b'test stream!')


def get_file_metadata_json():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)['file_metadata']

@pytest.fixture
def file_metadata_json():
    return get_file_metadata_json()


@pytest.fixture()
def file_metadata_resp(file_metadata_json):
    return json_resp(file_metadata_json)


@pytest.fixture()
def version_metadata_resp():
    return json_resp(from_fixture_json('versions_metadata'))


@pytest.fixture()
def version_metadata_object(file_metadata_object):
    return OsfMetadata.versions(file_metadata_object, from_fixture_json('versions_metadata')['data'])


@pytest.fixture()
def root_metadata_object():
    return OsfMetadata.root('osfstorage', 'guid0')


class FileMetadataRespFactory:
    def __new__(self):
        data = get_file_metadata_json()
        return json_resp(data)


def json_to_resp(key, status=200):
    json_data = from_fixture_json(key)
    return json_resp(json_data, status=status)

@pytest.fixture
def response_404():
    return json_resp(from_fixture_json('file_not_found_metadata'), status=404)


def children_resp():
    data = from_fixture_json('children_metadata')
    return json_resp(data)


def children_metadata():
    return from_fixture_json('children_metadata')


@pytest.fixture
def file_metadata_object(provider):
    return OsfMetadata(get_file_metadata_json()['data']['attributes'], provider.internal_provider, provider.resource)


@pytest.fixture
def folder_metadata_object(provider):
    return OsfMetadata(get_folder_metadata_json()['data']['attributes'], provider.internal_provider, provider.resource)


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
async def mock_file_download(aresponses, file_metadata_json, download_resp):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'GET', download_resp)


@pytest.fixture
async def mock_file_upload(aresponses, file_metadata_json):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'PUT', upload_resp())


@pytest.fixture
async def mock_create_folder(aresponses):
    path = '/v1/resources/guid0/providers/osfstorage/' + get_folder_metadata_json()['data']['id'] + '/'
    aresponses.add('files.osf.io', path, 'PUT', create_folder_resp())


@pytest.fixture
async def mock_file_missing(aresponses, file_metadata_json, response_404):
    aresponses.add('api.osf.io', response=response_404)


@pytest.fixture
async def mock_file_delete(aresponses, file_metadata_json, delete_resp):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'DELETE', delete_resp)


@pytest.fixture
async def mock_rename(aresponses, file_metadata_json, file_metadata_resp):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'POST', file_metadata_resp)


@pytest.fixture
async def mock_children(aresponses):
    path = '/v1/resources/guid0/providers/osfstorage/' + get_folder_metadata_json()['data']['id'] + '/'
    aresponses.add('files.osf.io', path, 'GET', children_resp())

@pytest.fixture
async def mock_intra_copy(aresponses, file_metadata_json):
    path = '/v1/resources/guid0/providers/osfstorage/' + file_metadata_json['data']['id']
    aresponses.add('files.osf.io', path, 'POST', file_metadata_resp)
