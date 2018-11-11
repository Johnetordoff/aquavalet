import asyncio
from tests.utils import json_resp, data_resp
from aresponses import ResponsesMockServer


class MockOsfstorageServer(ResponsesMockServer):

    def __init__(self):
        super().__init__(loop=asyncio.get_event_loop())

    def mock_api_get(self, metadata):
        resp = json_resp(metadata)
        self.add('api.osf.io', '/v2/files/' + metadata['data']['id'], 'GET', resp)

    def mock_waterbutler_get(self, metadata, data):
        resp = data_resp(data)
        self.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage/' + metadata['data']['id'], 'GET', resp)

    def mock_download(self, metadata, data):
        resp = json_resp(metadata)
        self.add('api.osf.io', '/v2/files/' + metadata['data']['id'], 'GET', resp)
        resp = data_resp(data)
        self.add('files.osf.io', '/v1/resources/guid0/providers/osfstorage/' + metadata['data']['id'], 'GET', resp)
