import os
import hashlib
import mimetypes

from aquavalet import metadata


class BaseOsfStyleItemMetadata(metadata.BaseMetadata):

    def __init__(self, raw, internal_provider, resource):
        super().__init__(raw)

        self.internal_provider = internal_provider
        self.resource = resource

        self.default_segments = [self.provider, internal_provider, resource]


    @classmethod
    def root(cls, internal_provider, resource):
        raw = {
            'name': f'{internal_provider} root',
            'kind': 'folder',
            'modified': '',
            'etag': '',
            'path': '/',
        }
        return cls(raw, internal_provider, resource)

    @classmethod
    def versions(cls, item, version_data):
        raw = item.raw
        versions = []
        for metadata in version_data:
            raw.update(metadata['attributes'])
            data = raw.copy()
            version = cls(data, item.internal_provider, item.resource)
            versions.append(version)

        return versions

    @classmethod
    def list(cls, item, data):
        items = []
        for metadata in data:
            print(metadata['attributes'])
            item = cls(metadata['attributes'], item.internal_provider, item.resource)
            items.append(item)

        return items

    @property
    def name(self):
        return self.raw['name']

    @property
    def kind(self):
        return self.raw['kind']

    @property
    def parent(self):
        if self.is_root:
            return '/'

    @property
    def size(self):
        if self.is_file:
            return self.raw['size']

    @property
    def is_file(self):
        return self.raw['kind'] == 'file'

    @property
    def is_folder(self):
        return self.raw['kind'] == 'folder'

    @property
    def is_root(self):
        return self.raw['path'] == '/'

    @property
    def modified(self):
        # TODO: standardize datetime
        return self.raw.get('date_modified') or self.raw.get('modified_utc')

    @property
    def guid(self):
        return self.raw.get('guid')

    @property
    def version_id(self):
        return self.raw.get('version') or self.raw.get('current_version')

    @property
    def created(self):
        # TODO: standardize datetime
        return self.raw.get('date_created') or self.raw.get('created_utc')

    @property
    def unix_path(self):
        if self.is_root:
            return '/'
        return self.raw.get('materialized') or self.raw.get('materialized_path')

    @property
    def etag(self):
        return self.raw.get('etag')

    @property
    def id(self):
        return self.raw['path']

    @property
    def path(self):
        return self.raw['path']

    @property
    def md5(self):
        if self.is_file:
            return self.raw['extra']['hashes']['md5']

    @property
    def sha256(self):
        if self.is_file:
            return self.raw['extra']['hashes']['sha256']

    @property
    def mimetype(self):
        _, ext = os.path.splitext(self.name)
        return mimetypes.types_map.get(ext)

    def serialized(self) -> dict:
        _, ext = os.path.splitext(self.name)
        return {
            'kind': self.kind,
            'name': self.name,
            'path': self.id,
            'unix_path': self.unix_path,
            'size': self.size,
            'created': self.created,
            'modified': self.modified,
            'mimetype': self.mimetype,
            'provider': self.provider,
            'md5': self.md5,
            'sha256': self.sha256,
            'etag': hashlib.sha256('{}::{}'.format(self.provider, self.etag).encode('utf-8')).hexdigest(),
            'version_id': self.version_id,
        }

