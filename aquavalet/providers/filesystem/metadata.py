import os
from aquavalet.core import metadata


class BaseFileSystemMetadata(metadata.BaseMetadata):

    def __init__(self, raw, path):
        super().__init__(raw, path)

    @property
    def provider(self):
        return 'filesystem'


class FileSystemItemMetadata(BaseFileSystemMetadata, metadata.BaseMetadata):

    @classmethod
    def path(cls, path):

        raw = {
            'name' : path.split('/')[-1],
            'path': path
        }

        return cls(raw, path)

    @property
    def id(self):
        return self.raw['path']

    @property
    def name(self):
        return os.path.split(self.raw['path'])[-1]

    @property
    def size(self):
        return self.raw['size']

    @property
    def modified(self):
        return self.raw['modified']

    @property
    def content_type(self):
        return self.raw['mime_type']

    @property
    def etag(self):
        return '{}::{}'.format(self.raw.get('modified'), self.raw['path'])

    @property
    def kind(self):
        return self.raw['kind']
