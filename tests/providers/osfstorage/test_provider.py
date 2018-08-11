import pytest

from .fixtures import (
    provider,
    folder_metadata,
    file_metadata_resp,
    file_metadata_json
)

from aquavalet.providers.osfstorage.metadata import OsfMetadata

class TestValidateItem:

    @pytest.mark.asyncio
    async def test_validate_item(self, provider, file_metadata_resp, aresponses):
        aresponses.add('api.osf.io', '/v2/files/5b6ee0c390a7e0001986aff5/', 'get', file_metadata_resp)
        item = await provider.validate_item('/osfstorage/guid0/5b6ee0c390a7e0001986aff5' )

        assert isinstance(item, OsfMetadata)

        assert item.id == '/5b6ee0c390a7e0001986aff5'
        assert item.path == '/5b6ee0c390a7e0001986aff5'
        assert item.name == 'test.txt'
        assert item.kind == 'file'
        assert item.mimetype == 'text/plain'

