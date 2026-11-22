import io
from pathlib import Path
from typing import BinaryIO, assert_type

from aiogram import Bot
from aiogram.client.bot import DownloadStream
from aiogram.client.session.base import DownloadTimeout


async def check(bot: Bot) -> None:
    assert_type(await bot.download("id", "x.bin"), None)
    assert_type(await bot.download("id", Path("x.bin")), None)
    assert_type(await bot.download("id", io.BytesIO()), io.BytesIO)
    assert_type(await bot.download_file("path", io.BytesIO()), io.BytesIO)
    assert_type(await bot.download("id"), BinaryIO)
    assert_type(await bot.download_file("path", "x.bin", timeout=5), None)
    assert_type(await bot.download_file("path", timeout=DownloadTimeout(total=5)), BinaryIO)
    assert_type(bot.stream("id", chunk_size=1024), DownloadStream)
    async with bot.stream("id") as stream:
        async for chunk in stream:
            assert_type(chunk, bytes)
