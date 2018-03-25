import os
from aquavalet.core import metadata


class BaseFileSystemMetadata(metadata.BaseMetadata):

    def __init__(self, raw, folder, path):
        super().__init__(raw)
        self._folder = folder
        self.path_obj = path

    @property
    def provider(self):
        return 'filesystem'

    def build_path(self, path):
        if path.lower().startswith(self._folder.lower()):
            path = path[len(self._folder):]
        return super().build_path(path)

class FileSystemItemMetadata(BaseFileSystemMetadata, metadata.BaseMetadata):

    @property
    def name(self):
        return self.raw.get('name') or os.path.split(self.raw['path'])[1]

    @property
    def path(self):
        return self.build_path(self.raw['path'])

    @property
    def size(self):
        return self.raw['size']

    @property
    def modified(self):
        return self.raw['modified']

    @property
    def created_utc(self):
        return None

    @property
    def content_type(self):
        return self.raw['mime_type']

    @property
    def etag(self):
        return '{}::{}'.format(self.raw.get('modified'), self.raw['path'])

    @property
    def kind(self):
        return self.raw['kind']
