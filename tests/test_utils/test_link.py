from typing import Any, Dict

import pytest

from aiogram.utils.link import create_telegram_link, create_tg_link


class TestLink:
    @pytest.mark.parametrize(
        "base,params,result",
        [["user", dict(id=42), "tg://user?id=42"]],
    )
    def test_create_tg_link(self, base: str, params: Dict[str, Any], result: str):
        assert create_tg_link(base, **params) == result

    @pytest.mark.parametrize(
        "base,params,result",
        [
            ["username", dict(), "https://t.me/username"],
            ["username", dict(start="test"), "https://t.me/username?start=test"],
        ],
    )
    def test_create_telegram_link(self, base: str, params: Dict[str, Any], result: str):
        assert create_telegram_link(base, **params) == result
