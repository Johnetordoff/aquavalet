import os

import pytest

from aquavalet.providers.filesystem.metadata import FileSystemMetadata


class TestMetadata:
    def test_file_metadata(self, fs):
        fs.create_file("/test.txt", contents=b"test")

        data = FileSystemMetadata(path="/test.txt")
        assert data.path == "/test.txt"
        assert data.provider == "filesystem"

        # Can't really assert this without time travel
        # assert data.modified == '2018-10-27T16:43:22.162256+00:00'
        # assert data.modified_utc == '2017-09-20T15:16:02.601916+00:00'
        # assert data.etag == ('Wed, 20 Sep 2017 15:16:02 +0000::/'
        #                    'code/website/osfstoragecache/77094244-aa24-48da-9437-d8ce6f7a94e9')

        assert data.mime_type == "text/plain"
        assert data.name == "test.txt"
        assert data.size == 4
        assert data.kind == "file"

        json_api_data = data.json_api_serialized()

        assert json_api_data["id"] == "/test.txt"
        assert json_api_data["type"] == "files"
        assert json_api_data["attributes"]["kind"] == "file"
        assert json_api_data["attributes"]["mimetype"] == "text/plain"
        assert json_api_data["attributes"]["size"] == 4
        assert json_api_data["attributes"]["provider"] == "filesystem"

        assert (
            json_api_data["links"]["info"]
            == "http://localhost:7777/filesystem/test.txt?serve=meta"
        )
        assert (
            json_api_data["links"]["delete"]
            == "http://localhost:7777/filesystem/test.txt?serve=delete"
        )
        assert (
            json_api_data["links"]["download"]
            == "http://localhost:7777/filesystem/test.txt?serve=download"
        )

        assert not "upload" in json_api_data["links"]
        assert not "children" in json_api_data["links"]

    def test_root_metadata(self, fs):
        data = FileSystemMetadata(path="/")
        assert data.path == "/"
        assert data.provider == "filesystem"

        assert data.mime_type is None
        assert data.name == "filesystem root"
        assert data.size == 0
        assert data.kind == "folder"

        json_api_data = data.json_api_serialized()

        assert json_api_data["id"] == "/"
        assert json_api_data["type"] == "files"
        assert json_api_data["attributes"]["kind"] == "folder"
        assert json_api_data["attributes"]["mimetype"] == None
        assert json_api_data["attributes"]["size"] == 0
        assert json_api_data["attributes"]["provider"] == "filesystem"

        assert (
            json_api_data["links"]["info"]
            == "http://localhost:7777/filesystem/?serve=meta"
        )
        assert (
            json_api_data["links"]["delete"]
            == "http://localhost:7777/filesystem/?serve=delete"
        )
        assert (
            json_api_data["links"]["download_as_zip"]
            == "http://localhost:7777/filesystem/?serve=download_as_zip"
        )
        assert (
            json_api_data["links"]["upload"]
            == "http://localhost:7777/filesystem/?serve=upload"
        )
        assert (
            json_api_data["links"]["children"]
            == "http://localhost:7777/filesystem/?serve=children"
        )

    def test_folder_metadata(self, fs):
        fs.create_dir("/folder test/")

        data = FileSystemMetadata(path="folder test/")
        assert data.path == "folder test/"
        assert data.provider == "filesystem"

        assert data.mime_type is None
        assert data.name == "folder test"
        assert data.size == 0
        assert data.kind == "folder"

        json_api_data = data.json_api_serialized()

        assert json_api_data["id"] == "folder test/"
        assert json_api_data["type"] == "files"
        assert json_api_data["attributes"]["kind"] == "folder"
        assert json_api_data["attributes"]["mimetype"] == None
        assert json_api_data["attributes"]["size"] == 0
        assert json_api_data["attributes"]["provider"] == "filesystem"

        assert (
            json_api_data["links"]["info"]
            == "http://localhost:7777/filesystem/folder%20test/?serve=meta"
        )
        assert (
            json_api_data["links"]["delete"]
            == "http://localhost:7777/filesystem/folder%20test/?serve=delete"
        )
        assert (
            json_api_data["links"]["download_as_zip"]
            == "http://localhost:7777/filesystem/folder%20test/?serve=download_as_zip"
        )
        assert (
            json_api_data["links"]["upload"]
            == "http://localhost:7777/filesystem/folder%20test/?serve=upload"
        )
        assert (
            json_api_data["links"]["children"]
            == "http://localhost:7777/filesystem/folder%20test/?serve=children"
        )
