import os
import hashlib
import mimetypes

from aquavalet import metadata


class BaseOsfStyleItemMetadata(metadata.BaseMetadata):
    def __init__(self, raw, internal_provider, resource):
        super().__init__(raw["attributes"])
        self.raw = raw
        self.internal_provider = internal_provider
        self.resource = resource

        self.default_segments = [self.provider, internal_provider, resource]

    @classmethod
    def root(cls, internal_provider, resource):
        data = {
            "attributes": {
                "name": f"{internal_provider} root",
                "kind": "folder",
                "modified": "",
                "etag": "",
                "path": "/",
            }
        }
        return cls(data, internal_provider, resource)

    @classmethod
    def versions(cls, item, version_data):
        raw = item.raw.copy()
        versions = []
        import pprint

        for ind, metadata in enumerate(version_data):
            data = raw.copy()
            data["attributes"].update(metadata["attributes"])
            pprint.pprint(data)
            version = cls(data.copy(), item.internal_provider, item.resource)
            assert data["attributes"]["version"] == str(2 - ind)
            versions.append(version)

        return versions

    @classmethod
    def list(cls, item, data):
        items = []
        for metadata in data:
            item = cls(metadata, item.internal_provider, item.resource)
            items.append(item)

        return items

    @property
    def name(self):
        return self.attributes["name"]

    @property
    def kind(self):
        return self.attributes["kind"]

    @property
    def parent(self):
        if self.is_root:
            return "/"

    @property
    def size(self):
        if self.is_file:
            return self.attributes["size"]

    @property
    def is_file(self):
        return self.attributes["kind"] == "file"

    @property
    def is_folder(self):
        return self.attributes["kind"] == "folder"

    @property
    def is_root(self):
        return self.attributes["path"] == "/"

    @property
    def modified(self):
        # TODO: standardize datetime
        return self.raw.get("date_modified") or self.raw.get("modified_utc")

    @property
    def guid(self):
        return self.attributes.get("guid")

    @property
    def version_id(self):
        return self.attributes.get("version") or self.attributes.get("current_version")

    @property
    def created(self):
        # TODO: standardize datetime
        return self.attributes.get("date_created") or self.attributes.get("created_utc")

    @property
    def unix_path(self):
        if self.is_root:
            return "/"
        return self.attributes.get("materialized") or self.attributes.get(
            "materialized_path"
        )

    @property
    def etag(self):
        return self.attributes.get("etag")

    @property
    def id(self):
        return self.attributes["path"]

    @property
    def path(self):
        return self.attributes["path"]

    @property
    def md5(self):
        extra = self.attributes.get("extra")
        if extra:
            return extra["hashes"]["md5"]

    @property
    def sha256(self):
        extra = self.attributes.get("extra")
        if extra:
            return extra["hashes"]["sha256"]

    @property
    def mimetype(self):
        _, ext = os.path.splitext(self.name)
        return mimetypes.types_map.get(ext)

    def serialized(self) -> dict:
        _, ext = os.path.splitext(self.name)
        return {
            "kind": self.kind,
            "name": self.name,
            "path": self.id,
            "unix_path": self.unix_path,
            "size": self.size,
            "created": self.created,
            "modified": self.modified,
            "mimetype": self.mimetype,
            "provider": self.provider,
            "md5": self.md5,
            "sha256": self.sha256,
            "etag": hashlib.sha256(
                "{}::{}".format(self.provider, self.etag).encode("utf-8")
            ).hexdigest(),
            "version_id": self.version_id,
        }
