import io
import json
import zipfile

import pytest

from .utils import (
    MockOsfstorageServer,
)

from .fixtures import (
    app,
    from_fixture_json,
    get_file_metadata_json,
    children_metadata,
    FileMetadataRespFactory,
)

build_path = lambda file_metadata: URL.build(
    path="/osfstorage/osfstorage/guid0/{}".format(file_metadata["data"]["id"])
).human_repr()

from tests.core.test_provider import BaseProviderTestSuite

from yarl import URL

from aioresponses import aioresponses


class TestOsfStorageProvider(BaseProviderTestSuite):
    @aioresponses()
    @pytest.mark.gen_test
    async def test_metadata(self, http_server_client, m):
        raise Exception(http_server_client)
        file_metadata = {}
        url = build_path(file_metadata)
        with aioresponses() as m:
            m.put(url, payload=file_metadata)
        response = await http_server_client.fetch(
            url, method="METADATA", allow_nonstandard_methods=True
        )

        assert response.code == 200
        resp = json.loads(response.body)
        assert resp["data"]["id"] == "/5b6ee0c390a7e0001986aff5"
        assert resp["data"]["attributes"]["name"] == "test.txt"
        assert resp["data"]["attributes"]["kind"] == "file"

    @pytest.mark.gen_test
    async def test_validate_item(self, http_server_client):
        with MockOsfstorageServer() as server:
            file_metadata = server.get_file_json()
            url = build_path(file_metadata)
            server.mock_metadata(file_metadata)
            response = await http_server_client.fetch(
                url, method="METADATA", allow_nonstandard_methods=True
            )

        assert response.code == 200
        resp = json.loads(response.body)
        assert resp["data"]["id"] == "/5b6ee0c390a7e0001986aff5"
        assert resp["data"]["attributes"]["name"] == "test.txt"
        assert resp["data"]["attributes"]["kind"] == "file"

    @pytest.mark.gen_test
    async def test_children(self, http_server_client):

        with MockOsfstorageServer() as server:
            file_metadata = server.get_file_item()
            folder_metadata = server.get_folder_item()
            url = build_path(file_metadata)

            url = build_path(file_metadata)
            server.mock_metadata(folder_metadata)
            server.mock_children(folder_metadata, children_metadata=children_metadata())
            response = await http_server_client.fetch(
                url, method="CHILDREN", allow_nonstandard_methods=True
            )

        assert response.code == 200
        resp = json.loads(response.body)
        assert resp["data"][0]["attributes"]["name"] == "test_folder"
        assert resp["data"][1]["attributes"]["name"] == "test.txt"

    @pytest.mark.gen_test
    async def test_delete(self, http_server_client):
        file_metadata = get_file_metadata_json()
        path = make_path(
            "osfstorage", "osfstorage", "guid0", file_metadata["data"]["id"]
        )

        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata)
            server.mock_delete(file_metadata)

            response = await http_server_client.fetch(
                path, method="DELETE", allow_nonstandard_methods=True
            )

        assert response.code == 204
        assert response.body == b""

    @pytest.mark.gen_test
    async def test_download(self, http_server_client):
        file_metadata = get_file_metadata_json()
        path = make_path(
            "osfstorage", "osfstorage", "guid0", file_metadata["data"]["id"]
        )

        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata)
            server.mock_download(file_metadata, b"test stream!")

            response = await http_server_client.fetch(
                path, method="DOWNLOAD", allow_nonstandard_methods=True
            )

        assert response.code == 200
        assert response.body == b"test stream!"

    @pytest.mark.gen_test
    async def test_download_range(self, http_server_client):
        file_metadata = get_file_metadata_json()
        path = make_path(
            "osfstorage",
            "osfstorage",
            "guid0",
            file_metadata["data"]["id"],
            range=(0, 3),
        )

        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata)
            server.mock_download(file_metadata, b"test")

            response = await http_server_client.fetch(
                path, method="DOWNLOAD", allow_nonstandard_methods=True
            )

        assert response.code == 200
        assert response.body == b"test"

    @pytest.mark.gen_test
    async def test_download_version(self, http_server_client):
        file_metadata = get_file_metadata_json()
        path = make_path(
            "osfstorage", "osfstorage", "guid0", file_metadata["data"]["id"], version=2
        )

        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata)
            server.mock_download_version(file_metadata, b"test stream")

            response = await http_server_client.fetch(
                path, method="DOWNLOAD", allow_nonstandard_methods=True
            )

        assert response.code == 200
        assert response.body == b"test stream"

    @pytest.mark.gen_test
    async def test_download_direct(self, http_server_client):
        raise NotImplementedError()

    @pytest.mark.gen_test
    async def test_download_zip(self, http_server_client):
        file_metadata = get_file_metadata_json()
        folder_metadata = get_folder_metadata_json()
        path = make_path(
            "osfstorage",
            "osfstorage",
            "guid0",
            folder_metadata["data"]["id"],
            serve="download_as_zip",
        )

        async with MockOsfstorageServer() as server:
            server.mock_metadata(folder_metadata)
            server.mock_children(folder_metadata, children_metadata=file_metadata)
            server.mock_download(file_metadata, b"test zip stream")

            resp = await http_server_client.fetch(
                path, method="GET", allow_nonstandard_methods=True
            )

        zip = zipfile.ZipFile(io.BytesIO(resp.body))

        # Verify CRCs
        assert zip.testzip() is None

        assert len(zip.infolist()) == 1

        # Check content of included files
        zipped1 = zip.open("/test.txt")
        assert zipped1.read() == b"test zip stream"

    @pytest.mark.gen_test
    async def test_intra_copy(self, http_server_client):
        file_metadata = get_file_metadata_json()
        path = make_path(
            "osfstorage",
            "osfstorage",
            "guid0",
            file_metadata["data"]["id"],
            to="/osfstorage/guid0/",
            destination_provider="osfstorage",
        )
        file_resp = FileMetadataRespFactory()

        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata)
            server.add(
                "files.osf.io",
                f'/v1/resources/guid0/providers/osfstorage/{file_metadata["data"]["id"]}',
                "POST",
                file_resp,
            )

            response = await http_server_client.fetch(
                path, method="COPY", allow_nonstandard_methods=True
            )

        assert response.code == 200

    @pytest.mark.gen_test
    async def test_versions(self, http_server_client):
        file_metadata = get_file_metadata_json()
        path = make_path(
            "osfstorage", "osfstorage", "guid0", file_metadata["data"]["id"]
        )

        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata)
            server.mock_versions(file_metadata, from_fixture_json("versions_metadata"))
            response = await http_server_client.fetch(
                path, method="VERSIONS", allow_nonstandard_methods=True
            )

        assert response.code == 200
        resp = json.loads(response.body)
        assert resp["data"][0]["attributes"]["version_id"] == "2"
        assert resp["data"][1]["attributes"]["version_id"] == "1"

    @pytest.mark.gen_test
    async def test_upload(self, http_server_client):
        path = make_path("osfstorage", "osfstorage", "guid0", new_name="test")

        async with MockOsfstorageServer() as server:
            server.mock_metadata(get_folder_metadata_json())
            server.mock_upload()

            response = await http_server_client.fetch(
                path, method="UPLOAD", allow_nonstandard_methods=True, body=b"12345"
            )

        assert response.code == 201

    @pytest.mark.gen_test
    async def test_upload_warn(self, http_server_client):
        folder_metadata = get_folder_metadata_json()
        path = make_path(
            "osfstorage",
            "osfstorage",
            "guid0",
            folder_metadata["data"]["id"],
            new_name="test",
            conflict="warn",
        )

        async with MockOsfstorageServer() as server:
            server.mock_metadata(folder_metadata)
            server.mock_409(folder_metadata)
            resp = await http_server_client.fetch(
                path, method="UPLOAD", allow_nonstandard_methods=True, raise_error=False
            )

        json_data = json.loads(resp.body)
        assert json_data["code"] == 409
        assert json_data["message"] == "Conflict 'test'."

    @pytest.mark.gen_test
    async def test_upload_new_version(self, http_server_client):
        folder_metadata = get_folder_metadata_json()
        path = make_path(
            "osfstorage",
            "osfstorage",
            "guid0",
            folder_metadata["data"]["id"],
            new_name="test",
            conflict="version",
        )

        old_version_metadata = get_file_metadata_json()
        old_version_metadata["data"]["id"] = "5b537030c86a8c001243ce7a"
        async with MockOsfstorageServer() as server:
            server.mock_metadata(folder_metadata)
            server.mock_409(folder_metadata)
            server.mock_upload(get_file_metadata_json())
            server.mock_children(folder_metadata)
            server.mock_upload(old_version_metadata)

            response = await http_server_client.fetch(
                path, method="UPLOAD", allow_nonstandard_methods=True, body=b"12345"
            )

        assert response.code == 201
        assert response.body == b""

    @pytest.mark.gen_test
    async def test_upload_replace(self, http_server_client):
        raise NotImplementedError()

    @pytest.mark.gen_test
    async def test_rename(self, http_server_client):
        file_metadata = get_file_metadata_json()
        path = make_path(
            "osfstorage",
            "osfstorage",
            "guid0",
            file_metadata["data"]["id"],
            new_name="new_name",
        )

        async with MockOsfstorageServer() as server:
            server.mock_metadata(file_metadata)
            server.mock_rename(file_metadata)

            response = await http_server_client.fetch(
                path, method="RENAME", allow_nonstandard_methods=True
            )

        assert response.code == 200
        assert response.body == b""

    @pytest.mark.gen_test
    async def test_create_folder(self, http_server_client):
        folder_metadata = get_folder_metadata_json()

        path = make_path(
            "osfstorage",
            "osfstorage",
            "guid0",
            folder_metadata["data"]["id"],
            new_name="new_test_folder",
        )

        async with MockOsfstorageServer() as server:
            server.mock_metadata(folder_metadata)
            server.mock_create_folder(folder_metadata)

            response = await http_server_client.fetch(
                path, method="CREATE_FOLDER", allow_nonstandard_methods=True
            )

        assert response.code == 201
        resp = json.loads(response.body)
        assert resp["data"]["id"] == "/5b9533710b4b7d000f1bdd90/"
        assert resp["data"]["attributes"]["name"] == "test_folder"
        assert resp["data"]["attributes"]["kind"] == "folder"
