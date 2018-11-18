import pytest
import json
import urllib.parse
import urllib

from .utils import MockOsfstorageServer

from .fixtures import (
    app,
    from_fixture_json,
    get_file_metadata_json,
    get_folder_metadata_json,
    FileMetadataRespFactory,
)


def make_url(base_url, *res, **params):
    url = base_url
    for r in res:
        url = '{}/{}'.format(url, r)
    if params:
        url = '{}/?{}'.format(url, urllib.parse.urlencode(params))
    print(url)
    return url


class TestMetadata:

    @pytest.mark.gen_test
    async def test_metadata(self, http_client, base_url):
        file_metadata = get_file_metadata_json()
        url = make_url(base_url, 'osfstorage', 'osfstorage', 'guid0', file_metadata["data"]["id"])
        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata)
            response = await http_client.fetch(url, method='METADATA', allow_nonstandard_methods=True)

        assert response.code == 200
        resp = json.loads(response.body)
        assert resp['data']['id'] == '/5b6ee0c390a7e0001986aff5'
        assert resp['data']['attributes']['name'] == 'test.txt'
        assert resp['data']['attributes']['kind'] == 'file'


class TestChildren:

    @pytest.mark.gen_test
    async def test_children(self, http_client, base_url):
        folder_metadata = get_folder_metadata_json()
        url = make_url(base_url, 'osfstorage', 'osfstorage', 'guid0', folder_metadata["data"]["id"])

        async with MockOsfstorageServer() as server:
            server.mock_metadata(folder_metadata)
            server.mock_children(folder_metadata)
            response = await http_client.fetch(url, method='CHILDREN', allow_nonstandard_methods=True)

        assert response.code == 200
        resp = json.loads(response.body)
        assert resp['data'][0]['attributes']['name'] == 'test-1'
        assert resp['data'][1]['attributes']['name'] == 'test-2'


class TestDelete:

    @pytest.mark.gen_test
    async def test_delete(self, http_client, base_url):
        file_metadata = get_file_metadata_json()
        url = make_url(base_url, 'osfstorage', 'osfstorage', 'guid0', file_metadata["data"]["id"])

        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata)
            server.mock_delete(file_metadata)

            response = await http_client.fetch(url, method='DELETE', allow_nonstandard_methods=True)

        assert response.code == 204
        assert response.body == b''


class TestDownload:
    @pytest.mark.gen_test
    async def test_download(self, http_client, base_url):
        file_metadata = get_file_metadata_json()
        url = make_url(base_url, 'osfstorage', 'osfstorage', 'guid0', file_metadata["data"]["id"])

        async with MockOsfstorageServer() as server:
            server.mock_download(file_metadata, b'test stream!')

            response = await http_client.fetch(url, method='DOWNLOAD', allow_nonstandard_methods=True)

        assert response.code == 200
        assert response.body == b'test stream!'


    @pytest.mark.gen_test
    async def test_download_version(self, http_client, base_url):
        raise NotImplementedError()


    @pytest.mark.gen_test
    async def test_download_direct(self, http_client, base_url):
        raise NotImplementedError()


class TestIntraCopy:

    @pytest.mark.gen_test
    async def test_intra_copy(self, http_client, base_url):
        file_metadata = get_file_metadata_json()
        url = make_url(base_url, 'osfstorage', 'osfstorage', 'guid0', file_metadata["data"]["id"], to='/osfstorage/guid0/', destination_provider='osfstorage')
        file_resp = FileMetadataRespFactory()

        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata)
            server.add('files.osf.io', f'/v1/resources/guid0/providers/osfstorage/{file_metadata["data"]["id"]}', 'POST', file_resp)

            response = await http_client.fetch(url, method='COPY', allow_nonstandard_methods=True)

        assert response.code == 200


class TestVersions:

    @pytest.mark.gen_test
    async def test_versions(self, http_client, base_url):
        file_metadata = get_file_metadata_json()
        url = make_url(base_url, 'osfstorage', 'osfstorage', 'guid0', file_metadata["data"]["id"])

        async with MockOsfstorageServer() as server:
            server.mock_versions(file_metadata, from_fixture_json('versions_metadata'))
            response = await http_client.fetch(url, method='VERSIONS', allow_nonstandard_methods=True)

        assert response.code == 200
        resp = json.loads(response.body)
        assert resp['data'][0]['attributes']['version_id'] == '2'
        assert resp['data'][1]['attributes']['version_id'] == '1'


class TestUpload:

    @pytest.mark.gen_test
    async def test_upload(self, http_client, base_url):
        url = make_url(base_url, 'osfstorage', 'osfstorage', 'guid0', new_name='test')

        async with MockOsfstorageServer() as server:
            server.mock_metadata(get_folder_metadata_json())
            server.mock_upload()

            response = await http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, body=b'12345')

        assert response.code == 201

    @pytest.mark.gen_test
    async def test_upload_warn(self, http_client, base_url):
        folder_metadata = get_folder_metadata_json()
        url = make_url(base_url, 'osfstorage', 'osfstorage', 'guid0', folder_metadata["data"]["id"], new_name='test', conflict='warn')

        async with MockOsfstorageServer() as server:
            server.mock_metadata(folder_metadata)
            server.mock_409(folder_metadata)
            resp = await http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, raise_error=False)

        json_data = json.loads(resp.body)
        assert json_data['code'] == 409
        assert json_data['message'] == "Conflict 'test'."

    @pytest.mark.gen_test
    async def test_upload_new_version(self, http_client, base_url):
        folder_metadata = get_folder_metadata_json()
        url = make_url(base_url, 'osfstorage', 'osfstorage', 'guid0', folder_metadata["data"]["id"], new_name='test', conflict='version')

        old_version_metadata = get_file_metadata_json()
        old_version_metadata['data']['id'] = '5b537030c86a8c001243ce7a'
        async with MockOsfstorageServer() as server:
            server.mock_metadata(folder_metadata)
            server.mock_409(folder_metadata)
            server.mock_upload(get_file_metadata_json())
            server.mock_children(folder_metadata)
            server.mock_upload(old_version_metadata)

            response = await http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, body=b'12345')

        assert response.code == 201

    @pytest.mark.gen_test
    async def test_upload_replace(self, http_client, base_url):
        raise NotImplementedError()


