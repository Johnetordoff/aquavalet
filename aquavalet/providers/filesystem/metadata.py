import os
from aquavalet.core import metadata



class FileSystemItemMetadata(metadata.BaseMetadata):

    def __init__(self, raw):
        self.raw = raw
        self.default_segments = [self.provider]


    @property
    def provider(self):
        return 'filesystem'

    @classmethod
    def build(cls, path):
        raw = {
            'name' : path.split('/')[-1],
            'path': path
        }

        return cls(raw)

    @property
    def id(self):
        return self.raw['path']

    @property
    def parent(self):
        path = self.raw['path'].rstrip('/')
        return '/'.join(os.path.split(path)[:-1]) + '/'

    @property
    def name(self):
        return os.path.split(self.raw['path'])[-1]

    def rename(self, new_name):
        self.raw['path'] = self.parent + new_name
        return self.path

    @property
    def path(self):
        return self.raw['path']

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
        if self.path.endswith('/'):
            return 'folder'
        return 'file'

    @property
    def is_file(self):
        return self.kind == 'file'

    @property
    def is_folder(self):
        return self.kind == 'folder'

    @property
    def is_root(self):
        return self.id == '/'