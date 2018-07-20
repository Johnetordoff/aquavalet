import os
import abc
import hashlib
import mimetypes
from urllib.parse import urlparse, quote

from aquavalet.core import utils
from aquavalet.server import settings


class BaseMetadata(metaclass=abc.ABCMeta):
    def __init__(self, raw: dict, path) -> None:

        self.raw = raw
        self.path = path
        self.default_segments = [self.provider]

    def serialized(self) -> dict:

        _, ext = os.path.splitext(self.name)
        return {
            'kind': self.kind,
            'name': self.name,
            'path': self.id,
            'modified': self.modified,
            'mimetype': mimetypes.types_map.get(ext),
            'provider': self.provider,
            'etag': hashlib.sha256('{}::{}'.format(self.provider, self.etag).encode('utf-8')).hexdigest(),
        }

    def json_api_serialized(self) -> dict:
        json_api = {
            'id': self.id,
            'type': 'files',
            'attributes': self.serialized(),
            'links': self._json_api_links(),
        }
        return json_api

    def _json_api_links(self) -> dict:
        actions = {}
        path_segments = [quote(seg) for seg in self.raw['path'].split('/') if seg]

        actions['info'] = self.construct_path(path_segments, 'meta')
        actions['delete'] = self.construct_path(path_segments, 'delete')
        actions['parent'] = self.construct_parent()

        if self.kind == 'folder':
            actions['children'] = self.construct_path(path_segments, 'children')
            actions['upload'] = self.construct_path(path_segments, 'upload')
        else:
            actions['download'] = self.construct_path(path_segments, 'download')

        return actions

    def construct_parent(self) -> str:
        print('path')
        print( self.parent)
        return urlparse(settings.DOMAIN + '/' + '/'.join(self.default_segments) + self.parent + '?serve=meta').geturl()

    def construct_path(self, path, action) -> str:
        segments = self.default_segments + path
        trailing_slash = '/' if self.kind == 'folder' or not path else ''
        return urlparse(settings.DOMAIN + '/' + '/'.join(segments) + trailing_slash + '?serve=' + action).geturl()

    @property
    @abc.abstractmethod
    def provider(self) -> str:
        """ The provider from which this resource originated. """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def kind(self) -> str:
        """ `file` or `folder` """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """ The user-facing name of the entity, excluding parent folder(s).
        ::

            /bar/foo.txt -> foo.txt
            /<someid> -> whatever.png
        """
        raise NotImplementedError

    @property
    def etag(self) -> str:
        raise NotImplementedError


    def __eq__(self, other: 'BaseMetadata') -> bool:  # type: ignore
        return isinstance(other, self.__class__) and self.serialized() == other.serialized()
