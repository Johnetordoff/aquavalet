import os
import hashlib
import mimetypes

from aquavalet.core import metadata


class BaseOsfStorageMetadata(metadata.BaseMetadata):

    @property
    def provider(self):
        return 'osfstorage'


class BaseOsfStorageItemMetadata(BaseOsfStorageMetadata):

    def __init__(self, raw, path, internal_provider, resource):
        super().__init__(raw, path)
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
        return cls(raw, '/', internal_provider, resource)

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
        return self.raw.get('modified')

    @property
    def unix_path(self):
        return self.raw.get('materialized')

    @property
    def etag(self):
        return self.raw.get('etag')

    @property
    def id(self):
        return self.raw['path']

    @property
    def path(self):
        return self.raw['path']

    def serialized(self) -> dict:
        _, ext = os.path.splitext(self.name)
        return {
            'kind': self.kind,
            'name': self.name,
            'path': self.id,
            'size': self.size,
            'modified': self.modified,
            'mimetype': mimetypes.types_map.get(ext),
            'provider': self.provider,
            'etag': hashlib.sha256('{}::{}'.format(self.provider, self.etag).encode('utf-8')).hexdigest(),
        }

