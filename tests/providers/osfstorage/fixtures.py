import io
import os
import json
from tests.utils import json_resp, data_resp

import pytest

from aquavalet.core import streams
from aquavalet.providers.osfstorage.provider import OSFStorageProvider
from aquavalet.providers.osfstorage.metadata import OsfMetadata

@pytest.fixture
def folder_children_metadata():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)['folder_children_metadata']


@pytest.fixture
def download_response():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)['download_response']


@pytest.fixture
def upload_response():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)['upload_response']

@pytest.fixture
def folder_metadata_json():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)['folder_metadata']

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
def revisions_metadata():
    with open(os.path.join(os.path.dirname(__file__), 'fixtures/fixtures.json'), 'r') as fp:
        return json.load(fp)['revisions_metadata']

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
def file_like(file_content):
    return io.BytesIO(file_content)


@pytest.fixture
def file_stream(file_like):
    return streams.FileStreamReader(file_like)

@pytest.fixture
def provider():
    provider = OSFStorageProvider({})
    provider.internal_provider = 'osfstorage'
    provider.resource = 'guid0'
    return provider
