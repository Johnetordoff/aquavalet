import pytest
from aquavalet.core.streams import RequestStreamReader


class TestRequestStream:

    @pytest.mark.asyncio
    async def test_request_stream(self, blob):
        RequestStreamReader

