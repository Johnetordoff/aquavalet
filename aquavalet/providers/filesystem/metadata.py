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
            'path': path
        }

        return cls(raw)

    @property
    def id(self):
        return self.raw['path']

    @property
    def parent(self):
        if os.path.dirname(self.raw['path'].rstrip('/')) == '/':
            return '/'

        if not self.is_root:
            return os.path.dirname(self.raw['path'].rstrip('/')) + '/'
        else:
            return '/'

    @property
    def name(self):
        return os.path.basename(self.raw['path'].rstrip('/'))

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