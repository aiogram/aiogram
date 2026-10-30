import datetime
import sys
from typing import Optional, Union

import pytest

from aiogram import F
from aiogram.filters.command import DeeplinkCommand
from aiogram.filters.command.data.base import DeeplinkData
from aiogram.filters.command.data.codecs import Base64Codec, PositionalCodec
from aiogram.types import Chat, Message
from tests.mocked_bot import MockedBot


def _msg(text: str) -> Message:
    return Message(
        message_id=1,
        text=text,
        chat=Chat(id=1, type="private"),
        date=datetime.datetime.now(),
    )


class MyOrder(DeeplinkData, prefix="order", codec=PositionalCodec(sep="_")):
    order_id: int
    promo: str | None = None


class TestDeeplinkCommand:
    def test_no_prefix_on_data_raises(self):
        class NoPfx(DeeplinkData):
            val: str

        with pytest.raises(ValueError, match="no prefix"):
            DeeplinkCommand(NoPfx)

class TestDeeplinkCommandFilter:
    @pytest.mark.parametrize(
        "text,expected_parsed",
        [
            (f"/start {MyOrder(order_id=42).pack()}", MyOrder(order_id=42)),
            (
                f"/start {MyOrder(order_id=7, promo='SALE').pack()}",
                MyOrder(order_id=7, promo="SALE"),
            ),
            ("/start wrongprefix99", False),
            ("/start", False),
        ],
    )
    async def test_call(self, text, expected_parsed, bot: MockedBot):
        result = await DeeplinkCommand(MyOrder)(_msg(text), bot)
        if expected_parsed is False:
            assert result is False
        else:
            assert result["command"].parsed == expected_parsed

    async def test_no_data_accepts_any_deeplink(self, bot: MockedBot):
        result = await DeeplinkCommand()(_msg("/start anything"), bot)
        assert result["command"].args == "anything"
        assert result["command"].parsed is None

    async def test_magic_on_parsed(self, bot: MockedBot):
        cmd = DeeplinkCommand(MyOrder, magic=F.parsed.order_id == 10)
        assert await cmd(_msg(f"/start {MyOrder(order_id=10).pack()}"), bot)
        assert not await cmd(_msg(f"/start {MyOrder(order_id=99).pack()}"), bot)

    async def test_base64_codec(self, bot: MockedBot):
        class MyB64(DeeplinkData, prefix="b", codec=Base64Codec(PositionalCodec(sep=" "))):
            text: str

        payload = MyB64(text="path/value").pack()
        result = await DeeplinkCommand(MyB64)(_msg(f"/start {payload}"), bot)
        assert result["command"].parsed == MyB64(text="path/value")

    async def test_encoded_class_roundtrip(self, bot: MockedBot):
        class EncodedOrder(DeeplinkData, prefix="order", encoded=True):
            order_id: int

        payload = EncodedOrder(order_id=7).pack()
        result = await DeeplinkCommand(EncodedOrder)(_msg(f"/start {payload}"), bot)
        assert result["command"].parsed == EncodedOrder(order_id=7)

    @pytest.mark.parametrize("hint", [Union[int, None], Optional[int]])
    async def test_optional_without_default(self, hint, bot: MockedBot):
        class MyData(DeeplinkData, prefix="x", codec=PositionalCodec(sep="_")):
            id: int
            extra: hint

        payload = MyData(id=1, extra=None).pack()
        result = await DeeplinkCommand(MyData)(_msg(f"/start {payload}"), bot)
        assert result["command"].parsed == MyData(id=1, extra=None)

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="UnionType requires Python 3.10+")
    async def test_optional_union_syntax(self, bot: MockedBot):
        class MyData(DeeplinkData, prefix="y", codec=PositionalCodec(sep="_")):
            id: int
            extra: int | None

        payload = MyData(id=2, extra=None).pack()
        result = await DeeplinkCommand(MyData)(_msg(f"/start {payload}"), bot)
        assert result["command"].parsed == MyData(id=2, extra=None)
