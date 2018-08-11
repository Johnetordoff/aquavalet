import os
import hashlib
import mimetypes

from aquavalet.core import metadata


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
        return self.raw.get('modified_utc')

    @property
    def created(self):
        return self.raw.get('created_utc')

    @property
    def unix_path(self):
        return self.raw.get('materialized') or self.raw.get('materialized_path')

    @property
    def unix_path_parent(self):
        if os.path.dirname(self.unix_path.rstrip('/')) == '/':
            return '/'

        return os.path.dirname(self.unix_path.rstrip('/')) + '/'

    @property
    def child_link(self):
        return self.BASE_URL + f'{self.resource}/providers/{self.internal_provider}{self.id}'

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
            'etag': hashlib.sha256('{}::{}'.format(self.provider, self.etag).encode('utf-8')).hexdigest(),
        }

