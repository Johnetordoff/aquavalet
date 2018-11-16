import pytest
import json
import urllib.parse


from .utils import MockOsfstorageServer

from .fixtures import (
    app,
    get_file_metadata_json,
    get_folder_metadata_json,
    get_version_json,
    download_resp,
    FileMetadataRespFactory,
    version_metadata_resp,
)

class TestMetadata:

    @pytest.mark.gen_test
    async def test_metadata(self, http_client, base_url):
        url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + get_file_metadata_json()['data']['id'])

        async with MockOsfstorageServer() as server:
            server.mock_api_get(get_file_metadata_json())
            response = await http_client.fetch(url, method='METADATA', allow_nonstandard_methods=True)

        assert response.code == 200
        resp = json.loads(response.body)
        assert resp['data']['id'] == '/5b6ee0c390a7e0001986aff5'
        assert resp['data']['attributes']['name'] == 'test.txt'
        assert resp['data']['attributes']['kind'] == 'file'


class TestChildren:

    @pytest.mark.gen_test
    async def test_children(self, http_client, base_url):
        url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + get_folder_metadata_json()['data']['id'])

        async with MockOsfstorageServer() as server:
            server.mock_api_get(get_folder_metadata_json())
            server.mock_children(get_folder_metadata_json())
            response = await http_client.fetch(url, method='CHILDREN', allow_nonstandard_methods=True)

        assert response.code == 200
        resp = json.loads(response.body)
        assert resp['data'][0]['attributes']['name'] == 'test-1'
        assert resp['data'][1]['attributes']['name'] == 'test-2'


class TestDownload:
    @pytest.mark.gen_test
    async def test_download(self, http_client, base_url):
        file_metadata = get_file_metadata_json()
        url = base_url + urllib.parse.quote(f'/osfstorage/osfstorage/guid0/{file_metadata["data"]["id"]}')

        async with MockOsfstorageServer() as server:
            server.mock_download(file_metadata, b'test stream!')

            response = await http_client.fetch(url, method='DOWNLOAD', allow_nonstandard_methods=True)

        assert response.code == 200
        assert response.body == b'test stream!'


class TestIntraCopy:
    @pytest.mark.gen_test
    async def test_intra_copy(self, http_client, base_url):
        file_metadata = get_file_metadata_json()

        url = base_url + urllib.parse.quote(f'/osfstorage/osfstorage/guid0/{file_metadata["data"]["id"]}') + '?to=/osfstorage/guid0/&destination_provider=osfstorage'
        file_resp = FileMetadataRespFactory()

        async with MockOsfstorageServer() as server:
            server.mock_api_get(file_metadata)
            server.add('files.osf.io', f'/v1/resources/guid0/providers/osfstorage/{file_metadata["data"]["id"]}', 'POST', file_resp)

            response = await http_client.fetch(url, method='COPY', allow_nonstandard_methods=True)

        assert response.code == 200


class TestVersions:

    @pytest.mark.gen_test
    async def test_versions(self, http_client, base_url):
        url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/' + get_file_metadata_json()['data']['id'])
        async with MockOsfstorageServer() as server:
            server.mock_versions(get_file_metadata_json(), get_version_json())
            response = await http_client.fetch(url, method='VERSIONS', allow_nonstandard_methods=True)

        assert response.code == 200
        resp = json.loads(response.body)
        assert resp['data'][0]['attributes']['version_id'] == '2'
        assert resp['data'][1]['attributes']['version_id'] == '1'


class TestUpload:

    @pytest.mark.gen_test
    async def test_upload(self, http_client, base_url):
        url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/') + '?new_name=test'

        async with MockOsfstorageServer() as server:
            server.mock_api_get(get_folder_metadata_json())
            server.mock_upload()

            response = await http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, body=b'12345')

        assert response.code == 201

    @pytest.mark.gen_test
    async def test_upload_warn(self, http_client, base_url):
        url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/') + get_folder_metadata_json()['data']['id'] + '?new_name=test&conflict=warn'

        async with MockOsfstorageServer() as server:
            server.mock_api_get(get_folder_metadata_json())
            server.mock_409(get_folder_metadata_json())
            resp = await http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, raise_error=False)

        json_data = json.loads(resp.body)
        assert json_data['code'] == 409
        assert json_data['message'] == "Conflict 'test'."

    @pytest.mark.gen_test
    async def test_upload_new_version(self, http_client, base_url):
        url = base_url + urllib.parse.quote('/osfstorage/osfstorage/guid0/') + get_folder_metadata_json()['data']['id'] + '?new_name=test-1&conflict=new_version'

        old_version_metadata = get_file_metadata_json()
        old_version_metadata['data']['id'] = '5b537030c86a8c001243ce7a'
        async with MockOsfstorageServer() as server:
            server.mock_api_get(get_folder_metadata_json())
            server.mock_409(get_folder_metadata_json())
            server.mock_upload(get_file_metadata_json())
            server.mock_children(get_folder_metadata_json())
            server.mock_upload(old_version_metadata)

            response = await http_client.fetch(url, method='UPLOAD', allow_nonstandard_methods=True, body=b'12345')

        assert response.code == 201


