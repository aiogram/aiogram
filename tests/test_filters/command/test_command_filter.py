import datetime

import pytest
from pydantic import BaseModel

from aiogram import F
from aiogram.filters import Command
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


class MyArgs(BaseModel):
    action: str
    target: str | None = None


class TestCommand:
    def test_codec_requires_data(self):
        with pytest.raises(ValueError):
            Command("do", codec=PositionalCodec(sep=" "))

    def test_no_data_codec_is_none(self):
        cmd = Command("ping")
        assert cmd.codec is None

    def test_explicit_codec_used(self):
        codec = PositionalCodec(sep=" ")
        cmd = Command("do", data=MyArgs, codec=codec)
        assert cmd.codec is codec

    def test_default_codec_is_positional_space(self):
        cmd = Command("do", data=MyArgs)
        assert isinstance(cmd.codec, PositionalCodec)
        assert cmd.codec.sep == " "


class TestCommandFilter:
    @pytest.mark.parametrize(
        "text,expected_parsed",
        [
            ("/do run server", MyArgs(action="run", target="server")),
            ("/do run", MyArgs(action="run")),
            ("/do a b c", False),
        ],
    )
    async def test_call(self, text, expected_parsed, bot: MockedBot):
        cmd = Command("do", data=MyArgs, codec=PositionalCodec(sep=" "))
        result = await cmd(_msg(text), bot)
        if expected_parsed is False:
            assert result is False
        else:
            assert result["command"].parsed == expected_parsed

    async def test_no_data_parsed_is_none(self, bot: MockedBot):
        result = await Command("ping")(_msg("/ping"), bot)
        assert result
        assert result["command"].parsed is None

    async def test_magic_on_parsed(self, bot: MockedBot):
        cmd = Command(
            "do", data=MyArgs, codec=PositionalCodec(sep=" "), magic=F.parsed.action == "run"
        )
        assert await cmd(_msg("/do run"), bot)
        assert not await cmd(_msg("/do stop"), bot)

    async def test_base64_codec_roundtrip(self, bot: MockedBot):
        codec = Base64Codec(PositionalCodec(sep=" "))
        cmd = Command("do", data=MyArgs, codec=codec)
        encoded = codec.encode(MyArgs(action="run", target="srv"))
        result = await cmd(_msg(f"/do {encoded}"), bot)
        assert result
        assert result["command"].parsed == MyArgs(action="run", target="srv")
