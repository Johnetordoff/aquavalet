import asyncio
from tests.utils import json_resp, data_resp
from aresponses import ResponsesMockServer

from functools import partial

from tests.providers.osfstorage.fixtures import (
    empty_resp,
    response_409,
    upload_resp,
    create_folder_resp,
    children_resp
)

from urllib.parse import urlencode


def make_path(*res, **params):
    url = ''
    for r in res:
        url = '{}/{}'.format(url, r)
    if params:
        url = '{}/?{}'.format(url, urlencode(params))
    return url


make_api_path = partial(make_path, 'v2', 'files')
make_files_path = partial(make_path, 'v1', 'resources', 'guid0', 'providers', 'osfstorage')


class MockOsfstorageServer(ResponsesMockServer):

    files_path = '/v1/resources/guid0/providers/osfstorage/{}'

    def __init__(self):
        super().__init__(loop=asyncio.get_event_loop())


    def mock_metadata(self, metadata):
        resp = json_resp(metadata)
        path = make_api_path(metadata["data"]["id"])
        self.add('api.osf.io', path, 'GET', resp, match_querystring=True)

    def mock_children(self, metadata, children_metadata=False):
        path = make_files_path(metadata['data']['id']) + '/'

        if children_metadata:
            if not isinstance(children_metadata['data'], list):
                children_metadata = {'data': [children_metadata['data']]}

            children_resp = json_resp(children_metadata)
            self.add('files.osf.io', path, 'GET', children_resp, match_querystring=True)
        else:
            self.add('files.osf.io', path, 'GET', json_resp({'data': []}, status=200), match_querystring=True)

    def mock_delete(self, metadata):
        self.add('files.osf.io',  make_files_path(metadata['data']['id']), 'DELETE', empty_resp(status=204))

    def mock_download(self, metadata, data):
        self.mock_metadata(metadata)
        resp = data_resp(data)
        if metadata['data']['attributes']['kind'] == 'folder':
            self.add('files.osf.io', make_files_path(metadata['data']['id']) + '/', 'GET', resp,
                     match_querystring=True)
        else:
            self.add('files.osf.io', make_files_path(metadata['data']['id']), 'GET', resp, match_querystring=True)

    def mock_download_version(self, metadata, data):
        self.mock_metadata(metadata)
        resp = data_resp(data)
        self.add('files.osf.io', make_files_path(metadata["data"]["id"] + '?version=2'), 'GET', resp, match_querystring=True)

    def mock_versions(self, metadata, version):
        self.mock_metadata(metadata)
        resp = json_resp(version)
        self.add('files.osf.io', make_files_path(metadata["data"]["id"] + '?versions='), 'GET', resp, match_querystring=True)

    def mock_upload(self, metadata=None):
        if metadata:
            self.add('files.osf.io', make_files_path(metadata["data"]["id"]), 'PUT', upload_resp())
        else:
            self.add('files.osf.io', make_files_path() + '/', 'PUT', upload_resp())

    def mock_rename(self, metadata):
        self.add('files.osf.io', f'/v1/resources/guid0/providers/osfstorage/{metadata["data"]["id"]}', 'POST', upload_resp())

    def mock_409(self, metadata=None):
        if metadata:
            self.add('files.osf.io',  make_files_path(metadata["data"]["id"]) + '/', 'PUT', response_409())
        else:
            self.add('files.osf.io',
                     make_files_path(metadata["data"]["id"]) + '/?kind=file&name=test&conflict=warn',
                     'PUT',
                     response_409(),
                     match_querystring=True)

    def mock_create_folder(self, metadata):
        path = make_files_path(metadata["data"]["id"] + '/?kind=folder&name=new_test_folder')
        self.add('files.osf.io', path, 'PUT', create_folder_resp(), match_querystring=True)

