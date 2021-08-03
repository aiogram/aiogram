from typing import Dict, Optional

import pytest

from aiogram import Bot
from aiogram.methods.base import prepare_parse_mode
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


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
    async def test_default_parse_mode(
        self, bot: MockedBot, parse_mode: str, data: Dict[str, str], result: Optional[str]
    ):
        async with Bot(token="42:TEST", parse_mode=parse_mode).context() as bot:
            assert bot.parse_mode == parse_mode
            prepare_parse_mode(bot, data)
            assert data.get("parse_mode") == result

    async def test_list(self):
        data = [{}] * 2
        data.append({"parse_mode": "HTML"})
        bot = Bot(token="42:TEST", parse_mode="Markdown")
        prepare_parse_mode(bot, data)

        assert isinstance(data, list)
        assert len(data) == 3
        assert all("parse_mode" in item for item in data)
        assert data[0]["parse_mode"] == "Markdown"
        assert data[1]["parse_mode"] == "Markdown"
        assert data[2]["parse_mode"] == "HTML"

    def test_bot_not_in_context(self, bot: MockedBot):
        data = {}
        prepare_parse_mode(bot, data)
        assert data["parse_mode"] is None
