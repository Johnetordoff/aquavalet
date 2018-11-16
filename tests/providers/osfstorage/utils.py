import asyncio
from tests.utils import json_resp, data_resp
from aresponses import ResponsesMockServer

from tests.providers.osfstorage.fixtures import response_409, upload_resp, children_resp

class MockOsfstorageServer(ResponsesMockServer):

    def __init__(self):
        super().__init__(loop=asyncio.get_event_loop())

    def mock_api_get(self, metadata):
        resp = json_resp(metadata)
        self.add('api.osf.io', '/v2/files/' + metadata['data']['id'], 'GET', resp, match_querystring=True)

    def mock_waterbutler_get(self, metadata, data):
        resp = data_resp(data)
        self.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage/' + metadata['data']['id'], 'GET', resp, match_querystring=True)

    def mock_children(self, metadata):
        self.add('files.osf.io', f'/v1/resources/guid0/providers/osfstorage/{metadata["data"]["id"]}/', 'GET', children_resp(), match_querystring=True)

    def mock_download(self, metadata, data):
        resp = json_resp(metadata)
        self.add('api.osf.io', '/v2/files/' + metadata['data']['id'], 'GET', resp)
        resp = data_resp(data)
        self.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage/' + metadata['data']['id'], 'GET', resp)

    def mock_versions(self, metadata, version):
        self.mock_api_get(metadata)
        resp = json_resp(version)
        self.add('files.osf.io', f'/v1/resources/guid0/providers/osfstorage/{metadata["data"]["id"]}?versions=', 'GET', resp, match_querystring=True)

    def mock_upload(self, metadata=None):
        if metadata:
            self.add('files.osf.io', f'/v1/resources/guid0/providers/osfstorage/{metadata["data"]["id"]}/', 'PUT', upload_resp())
        else:
            self.add('files.osf.io', f'/v1/resources/guid0/providers/osfstorage/', 'PUT', upload_resp())

    def mock_409(self, metadata=None):
        if metadata:
            self.add('files.osf.io', f'/v1/resources/guid0/providers/osfstorage/{metadata["data"]["id"]}/', 'PUT', response_409())
        else:
            self.add('files.osf.io',
                     f'/v1/resources/guid0/providers/osfstorage/{metadata["data"]["id"]}/?kind=file&name=test&conflict=warn',
                     'PUT',
                     response_409(),
                     )
