import asyncio

import pytest


class TestNothing:
    @pytest.mark.asyncio
    async def test_nothing(self):
        result = await asyncio.sleep(1, result=42)
        assert result == 42
