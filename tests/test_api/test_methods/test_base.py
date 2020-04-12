from typing import Dict, Optional

import pytest

from aiogram import Bot
from aiogram.api.methods.base import prepare_parse_mode


class TestPrepareFile:
    # TODO: Add tests
    pass


class TestPrepareInputMedia:
    # TODO: Add tests
    pass


class TestPrepareMediaFile:
    # TODO: Add tests
    pass


class TestPrepareParseMode:
    @pytest.mark.parametrize(
        "parse_mode,data,result",
        [
            [None, {}, None],
            ["HTML", {}, "HTML"],
            ["Markdown", {}, "Markdown"],
            [None, {"parse_mode": "HTML"}, "HTML"],
            ["HTML", {"parse_mode": "HTML"}, "HTML"],
            ["Markdown", {"parse_mode": "HTML"}, "HTML"],
        ],
    )
    @pytest.mark.asyncio
    async def test_default_parse_mode(
        self, parse_mode: str, data: Dict[str, str], result: Optional[str]
    ):
        async with Bot(token="42:TEST", parse_mode=parse_mode).context() as bot:
            assert bot.parse_mode == parse_mode
            prepare_parse_mode(data)
            assert data.get("parse_mode") == result

    @pytest.mark.asyncio
    async def test_list(self):
        data = [{}] * 2
        data.append({"parse_mode": "HTML"})
        async with Bot(token="42:TEST", parse_mode="Markdown").context():
            prepare_parse_mode(data)

        assert isinstance(data, list)
        assert len(data) == 3
        assert all("parse_mode" in item for item in data)
        assert data[0]["parse_mode"] == "Markdown"
        assert data[1]["parse_mode"] == "Markdown"
        assert data[2]["parse_mode"] == "HTML"

    def test_bot_not_in_context(self):
        data = {}
        prepare_parse_mode(data)
        assert data["parse_mode"] is None
