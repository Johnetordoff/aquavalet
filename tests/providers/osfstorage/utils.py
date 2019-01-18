import asyncio
from tests.utils import json_resp, data_resp
from aioresponses import aioresponses

from functools import partial

from aquavalet.providers.osfstorage.metadata import OsfMetadata

from tests.providers.osfstorage.fixtures import (
    empty_resp,
    from_fixture_json
)
from yarl import URL


class MockOsfstorageServer(aioresponses):

    FILES_PATH = URL('v1/resources/guid0/providers/osfstorage/')
    METADATA_PATH = URL('/v2/files/')

    FILES_DOMAIN = URL('https://files.osf.io/')
    METADATA_DOMAIN = URL('https://api.osf.io/')

    def get_files_url(self, metadata):
        path = self.FILES_PATH / metadata['data']['id']
        if metadata["data"]['attributes']['kind'] == 'folder':
            path = self.FILES_PATH / (metadata['data']['id'] + '/')

        url = self.FILES_DOMAIN.join(path)
        return url

    def get_metadata_url(self, metadata):
        return self.METADATA_DOMAIN.join(self.METADATA_PATH) / metadata['data']['id']

    def get_file_json(self):
        return from_fixture_json('file_metadata')

    def get_file_item(self):
        return OsfMetadata(self.get_file_json()['data'], 'osfstorage', 'guid0')

    def get_children_json(self):
        return from_fixture_json('children_metadata')

    def get_folder_json(self):
        return from_fixture_json('folder_metadata')

    def get_folder_item(self):
        return OsfMetadata(self.get_folder_json()['data'], 'osfstorage', 'guid0')

    def get_version_json(self):
        return from_fixture_json('versions_metadata')

    def get_version_item(self):
        file_item = self.get_file_item()
        return OsfMetadata.versions(file_item, self.get_version_json()['data'])

    def mock_metadata(self, metadata):
        url = self.get_metadata_url(metadata)
        self.get(url, payload=metadata)

    def mock_children(self, metadata, children_metadata=False):
        url = self.get_files_url(metadata)

        if children_metadata:
            if not isinstance(children_metadata['data'], list):
                children_metadata = {'data': [children_metadata['data']]}
            self.get(url, payload=children_metadata)
        else:
            self.get(url, payload={'data': []})

    def mock_delete(self, metadata):
        url = self.get_files_url(metadata).with_query({'confirm_delete': 0})
        self.delete(url, status=204)

    def mock_download(self, metadata, data):
        url = self.get_files_url(metadata)

        if metadata['data']['attributes']['kind'] == 'folder':
            self.get(url, body=data, content_type='application/octet-stream')
        else:
            self.get(url, body=data, content_type='application/octet-stream')

    def mock_download_version(self, metadata, data):
        url = self.get_files_url(metadata).with_query({'version': 2})
        self.get(url, body=data, content_type='application/octet-stream')

    def mock_versions(self, metadata, versions):
        url = self.get_files_url(metadata)
        self.get(url, payload=versions)

    def mock_upload(self, metadata=None):
        upload = from_fixture_json('upload_metadata')
        url = self.get_files_url(metadata).with_query({'conflict': 'warn', 'kind': 'file', 'name': 'test.txt'})

        if metadata:
            self.put(url, payload=upload)
        else:
            self.put(url, payload=upload)

    def mock_rename(self, metadata):
        url = self.get_files_url(metadata)
        upload = from_fixture_json('upload_metadata')
        self.post(url, payload=upload)

    def mock_409(self, metadata=None):
        conflict = from_fixture_json('conflict_metadata')
        url = self.get_files_url(metadata["data"]["id"])

        if metadata:
            self.post(url,  payload=conflict)
        else:
            url = url.with_query({'kind': 'file', 'name': 'test', 'conflict': 'warn'})
            self.put(url, payload=conflict)

    def mock_create_folder(self, metadata):
        url = self.get_files_url(metadata).with_query({'kind': 'folder', 'name': 'new_test_folder'})
        print(url)
        self.put(url, payload=metadata, status=201)

