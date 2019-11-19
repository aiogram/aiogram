from typing import AsyncIterable

import pytest

from aiogram.api.types import BufferedInputFile, FSInputFile, InputFile


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
