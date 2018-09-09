import io
import os
import json

import aiohttp

from tests.utils import json_resp, data_resp, empty_resp

import pytest

from aquavalet.core import streams
from aquavalet.providers.osfstorage.provider import OSFStorageProvider
from aquavalet.providers.osfstorage.metadata import OsfMetadata

def from_fixture_json(key):
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)[key]


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
def file_metadata_resp(file_metadata_json):
    return json_resp(file_metadata_json)

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
def folder_metadata_object(folder_metadata):
    return OsfMetadata(folder_metadata['data'])

@pytest.fixture
def revision_metadata_object(revisions_metadata):
    return OsfMetadata(revisions_metadata['revisions'][0])

@pytest.fixture
def file_stream():
    return streams.FileStreamReader(io.BytesIO(b'Test Upload Content'))

@pytest.fixture
def provider():
    provider = OSFStorageProvider({})
    provider.internal_provider = 'osfstorage'
    provider.resource = 'guid0'
    return provider
