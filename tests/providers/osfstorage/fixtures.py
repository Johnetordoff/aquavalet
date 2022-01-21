import os
import asyncio
import json
import aioresponses

from tests.utils import json_resp, data_resp, empty_resp

import pytest
from aquavalet.providers.osfstorage.provider import OSFStorageProvider
from aquavalet.providers.osfstorage.metadata import OsfMetadata
from aquavalet.app import make_app


def from_fixture_json(key):
    with open(
        os.path.join(os.path.dirname(__file__), "fixtures/fixtures.json"), "r"
    ) as fp:
        return json.load(fp)[key]


@pytest.fixture
def app():
    return make_app(False)


@pytest.fixture
def folder_metadata_resp(folder_metadata_json):
    return json_resp(folder_metadata_json)


def get_file_metadata_json():
    with open(
        os.path.join(os.path.dirname(__file__), "fixtures/fixtures.json"), "r"
    ) as fp:
        return json.load(fp)["file_metadata"]


@pytest.fixture
def root_metadata_object():
    return OsfMetadata.root("osfstorage", "guid0")


class FileMetadataRespFactory:
    def __new__(self):
        data = get_file_metadata_json()
        return json_resp(data)


def json_to_resp(key, status=200):
    json_data = from_fixture_json(key)
    return json_resp(json_data, status=status)


def children_metadata():
    return from_fixture_json("children_metadata")


@pytest.fixture
def revision_metadata_object(revisions_metadata):
    return OsfMetadata(revisions_metadata["revisions"][0])


@pytest.fixture
def provider():
    provider = OSFStorageProvider({})
    provider.internal_provider = "osfstorage"
    provider.resource = "guid0"
    return provider
