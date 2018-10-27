import os

import pytest

from aquavalet.providers.filesystem.metadata import FileSystemMetadata


@pytest.fixture
def file_metadata():
    return {
        'path': '/test/test.txt',
        'modified_utc': '2017-09-20T15:16:02.601916+00:00',
        'size': 1234,
        'modified': 'Wed, 20 Sep 2017 15:16:02 +0000'
    }

@pytest.fixture
def root_metadata():
    return {
        'path': os.path.join('/')
    }

@pytest.fixture
def folder_metadata():
    return {
        'path': os.path.join('/', 'folder1/')
    }

@pytest.fixture
def subfolder_metadata():
    return {
        'path': os.path.join('/', 'folder1/', 'folder2/')
    }


class TestMetadata:

    def test_file_metadata(self, file_metadata, fs):

        fs.create_file('/test/test.txt', contents=b'test')
        assert os.path.exists('/test/test.txt')

        data = FileSystemMetadata(file_metadata)
        assert data.path == '/test/test.txt'
        assert data.provider == 'filesystem'

        # Can't really assert this without time travel
        #assert data.modified == '2018-10-27T16:43:22.162256+00:00'
        #assert data.modified_utc == '2017-09-20T15:16:02.601916+00:00'
        #assert data.etag == ('Wed, 20 Sep 2017 15:16:02 +0000::/'
         #                    'code/website/osfstoragecache/77094244-aa24-48da-9437-d8ce6f7a94e9')

        assert data.content_type == 'text/plain'
        assert data.name == 'test.txt'
        assert data.size == 4
        assert data.kind == 'file'

        json_api_data = data.json_api_serialized()

        assert json_api_data['id'] == '/test/test.txt'
        assert json_api_data['type'] == 'files'
        assert json_api_data['attributes']['kind'] == 'file'
        assert json_api_data['attributes']['mimetype'] == 'text/plain'
        assert json_api_data['attributes']['size'] == 4
        assert json_api_data['attributes']['provider'] == 'filesystem'

        assert json_api_data['links']['info'] == 'http://localhost:7777/filesystem/test/test.txt?serve=meta'
        assert json_api_data['links']['delete'] == 'http://localhost:7777/filesystem/test/test.txt?serve=delete'
        assert json_api_data['links']['download'] == 'http://localhost:7777/filesystem/test/test.txt?serve=download'

        assert not 'upload' in json_api_data['links']
        assert not 'children' in json_api_data['links']


    def test_root_metadata(self, root_metadata):
        data = FileSystemFolderMetadata(root_metadata, '')
        assert data.path == '/'
        assert data.name == ''
        assert data.provider == 'filesystem'
        assert data.build_path('') == '/'
        assert data.materialized_path == '/'
        assert data.is_folder is True
        assert data.children is None
        assert data.kind == 'folder'
        assert data.etag is None
        assert data.serialized() == {
            'extra': {},
            'kind': 'folder',
            'name': '',
            'path': '/',
            'provider': 'filesystem',
            'materialized': '/',
            'etag': '6a2b72b88f67692ff6f4cc3a52798cdc54a6e7c7e6dcbf8463fcb5105b6b949e'
        }

        assert data.json_api_serialized('7ycmyr') == {
            'id': 'filesystem/',
            'type': 'files',
            'attributes': {
                'extra': {},
                'kind': 'folder',
                'name': '',
                'path': '/',
                'provider': 'filesystem',
                'materialized': '/',
                'etag': '6a2b72b88f67692ff6f4cc3a52798cdc54a6e7c7e6dcbf8463fcb5105b6b949e',
                'resource': '7ycmyr',
                'size': None
            },
            'links': {
                'move': 'http://localhost:7777/v1/resources/7ycmyr/providers/filesystem/',
                'upload': ('http://localhost:7777/v1/resources/'
                    '7ycmyr/providers/filesystem/?kind=file'),
                'delete': 'http://localhost:7777/v1/resources/7ycmyr/providers/filesystem/',
                'new_folder': ('http://localhost:7777/v1/resources/'
                    '7ycmyr/providers/filesystem/?kind=folder')
            }
        }

        assert data._json_api_links('cn42d') == {
            'move': 'http://localhost:7777/v1/resources/cn42d/providers/filesystem/',
            'upload': ('http://localhost:7777/v1/resources/'
                'cn42d/providers/filesystem/?kind=file'),
            'delete': 'http://localhost:7777/v1/resources/cn42d/providers/filesystem/',
            'new_folder': ('http://localhost:7777/v1/resources/'
                'cn42d/providers/filesystem/?kind=folder')
        }

    def test_folder_metadata(self, folder_metadata):
        data = FileSystemItemMetadata(folder_metadata, '/')
        assert data.path == '/folder1/'
        assert data.name == 'folder1'
        assert data.provider == 'filesystem'
        assert data.build_path('') == '/'
        assert data.materialized_path == '/folder1/'
        assert data.is_folder is True
        assert data.children is None
        assert data.kind == 'folder'
        assert data.etag is None
        assert data.serialized() == {
            'extra': {},
            'kind': 'folder',
            'name': 'folder1',
            'path': '/folder1/',
            'provider': 'filesystem',
            'materialized': '/folder1/',
            'etag': '6a2b72b88f67692ff6f4cc3a52798cdc54a6e7c7e6dcbf8463fcb5105b6b949e'
        }

        assert data.json_api_serialized('7ycmyr') == {
            'id': 'filesystem/folder1/',
            'type': 'files',
            'attributes': {
                'extra': {},
                'kind': 'folder',
                'name': 'folder1',
                'path': '/folder1/',
                'provider': 'filesystem',
                'materialized': '/folder1/',
                'etag': '6a2b72b88f67692ff6f4cc3a52798cdc54a6e7c7e6dcbf8463fcb5105b6b949e',
                'resource': '7ycmyr',
                'size': None
            },
            'links': {
                'move': 'http://localhost:7777/v1/resources/7ycmyr/providers/filesystem/folder1/',
                'upload': ('http://localhost:7777/v1/resources/'
                    '7ycmyr/providers/filesystem/folder1/?kind=file'),
                'delete': 'http://localhost:7777/v1/resources/7ycmyr/providers/filesystem/folder1/',
                'new_folder': ('http://localhost:7777/v1/resources/'
                    '7ycmyr/providers/filesystem/folder1/?kind=folder')
            }
        }

        assert data._json_api_links('cn42d') == {
            'move': 'http://localhost:7777/v1/resources/cn42d/providers/filesystem/folder1/',
            'upload': ('http://localhost:7777/v1/resources/'
                'cn42d/providers/filesystem/folder1/?kind=file'),
            'delete': 'http://localhost:7777/v1/resources/cn42d/providers/filesystem/folder1/',
            'new_folder': ('http://localhost:7777/v1/resources/'
                'cn42d/providers/filesystem/folder1/?kind=folder')
        }

    def test_subfolder_metadata(self, subfolder_metadata):
        data = FileSystemItemMetadata(subfolder_metadata, '/')
        assert data.path == '/folder1/folder2/'
        assert data.name == 'folder2'
        assert data.provider == 'filesystem'
        assert data.build_path('') == '/'
        assert data.materialized_path == '/folder1/folder2/'
        assert data.is_folder is True
        assert data.children is None
        assert data.kind == 'folder'
        assert data.etag is None
        assert data.serialized() == {
            'extra': {},
            'kind': 'folder',
            'name': 'folder2',
            'path': '/folder1/folder2/',
            'provider': 'filesystem',
            'materialized': '/folder1/folder2/',
            'etag': '6a2b72b88f67692ff6f4cc3a52798cdc54a6e7c7e6dcbf8463fcb5105b6b949e'
        }

        assert data.json_api_serialized('7ycmyr') == {
            'id': 'filesystem/folder1/folder2/',
            'type': 'files',
            'attributes': {
                'extra': {},
                'kind': 'folder',
                'name': 'folder2',
                'path': '/folder1/folder2/',
                'provider': 'filesystem',
                'materialized': '/folder1/folder2/',
                'etag': '6a2b72b88f67692ff6f4cc3a52798cdc54a6e7c7e6dcbf8463fcb5105b6b949e',
                'resource': '7ycmyr',
                'size': None
            },
            'links': {
                'move': 'http://localhost:7777/v1/resources/7ycmyr/providers/filesystem/'
                        'folder1/folder2/',
                'upload': ('http://localhost:7777/v1/resources/'
                    '7ycmyr/providers/filesystem/folder1/folder2/?kind=file'),
                'delete': 'http://localhost:7777/v1/resources/7ycmyr/providers/filesystem/'
                          'folder1/folder2/',
                'new_folder': ('http://localhost:7777/v1/resources/'
                    '7ycmyr/providers/filesystem/folder1/folder2/?kind=folder')
            }
        }

        assert data._json_api_links('cn42d') == {
            'move': 'http://localhost:7777/v1/resources/cn42d/providers/filesystem'
                    '/folder1/folder2/',
            'upload': ('http://localhost:7777/v1/resources/'
                'cn42d/providers/filesystem/folder1/folder2/?kind=file'),
            'delete': 'http://localhost:7777/v1/resources/cn42d/providers/filesystem'
                      '/folder1/folder2/',
            'new_folder': ('http://localhost:7777/v1/resources/'
                'cn42d/providers/filesystem/folder1/folder2/?kind=folder')
        }
