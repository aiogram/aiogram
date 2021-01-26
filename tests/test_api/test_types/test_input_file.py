from typing import AsyncIterable

import pytest
from aresponses import ResponsesMockServer

from aiogram import Bot
from aiogram.types import BufferedInputFile, FSInputFile, InputFile, URLInputFile


class TestInputFile:
    def test_fs_input_file(self):
        file = FSInputFile(__file__)

        assert isinstance(file, InputFile)
        assert isinstance(file, AsyncIterable)
        assert file.filename is not None
        assert file.filename.startswith("test_")
        assert file.filename.endswith(".py")
        assert file.chunk_size > 0

    @pytest.mark.asyncio
    async def test_fs_input_file_readable(self):
        file = FSInputFile(__file__, chunk_size=1)

        assert file.chunk_size == 1

        size = 0
        async for chunk in file:
            chunk_size = len(chunk)
            assert chunk_size == 1
            size += chunk_size
        assert size > 0

    def test_buffered_input_file(self):
        file = BufferedInputFile(b"\f" * 10, filename="file.bin")

        assert isinstance(file, InputFile)
        assert isinstance(file, AsyncIterable)
        assert file.filename == "file.bin"
        assert isinstance(file.data, bytes)

    @pytest.mark.asyncio
    async def test_buffered_input_file_readable(self):
        file = BufferedInputFile(b"\f" * 10, filename="file.bin", chunk_size=1)

        size = 0
        async for chunk in file:
            chunk_size = len(chunk)
            assert chunk_size == 1
            size += chunk_size
        assert size == 10

    @pytest.mark.asyncio
    async def test_buffered_input_file_from_file(self):
        file = BufferedInputFile.from_file(__file__, chunk_size=10)

        assert isinstance(file, InputFile)
        assert isinstance(file, AsyncIterable)
        assert file.filename is not None
        assert file.filename.startswith("test_")
        assert file.filename.endswith(".py")
        assert isinstance(file.data, bytes)
        assert file.chunk_size == 10

    @pytest.mark.asyncio
    async def test_buffered_input_file_from_file_readable(self):
        file = BufferedInputFile.from_file(__file__, chunk_size=1)

        size = 0
        async for chunk in file:
            chunk_size = len(chunk)
            assert chunk_size == 1
            size += chunk_size
        assert size > 0

    @pytest.mark.asyncio
    async def test_uri_input_file(self, aresponses: ResponsesMockServer):
        aresponses.add(
            aresponses.ANY, aresponses.ANY, "get", aresponses.Response(status=200, body=b"\f" * 10)
        )

        Bot.set_current(Bot("42:TEST"))

        file = URLInputFile("https://test.org/", chunk_size=1)

        size = 0
        async for chunk in file:
            assert chunk == b"\f"
            chunk_size = len(chunk)
            assert chunk_size == 1
            size += chunk_size
        assert size == 10
