from __future__ import annotations

import io
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    AsyncGenerator,
    AsyncIterator,
    Iterator,
    Optional,
    Union,
)

import aiofiles as aiofiles

DEFAULT_CHUNK_SIZE = 64 * 1024  # 64 kb


class InputFile(ABC):
    """
    This object represents the contents of a file to be uploaded. Must be posted using
    multipart/form-data in the usual way that files are uploaded via the browser.

    Source: https://core.telegram.org/bots/api#inputfile
    """

    def __init__(self, filename: Optional[str] = None, chunk_size: int = DEFAULT_CHUNK_SIZE):
        self.filename = filename
        self.chunk_size = chunk_size

    @classmethod
    def __get_validators__(cls) -> Iterator[None]:
        yield None

    @abstractmethod
    async def read(self, chunk_size: int) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        yield b""

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self.read(self.chunk_size):
            yield chunk


class BufferedInputFile(InputFile):
    def __init__(self, file: bytes, filename: str, chunk_size: int = DEFAULT_CHUNK_SIZE):
        super().__init__(filename=filename, chunk_size=chunk_size)

        self.data = file

    @classmethod
    def from_file(
        cls,
        path: Union[str, Path],
        filename: Optional[str] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> BufferedInputFile:
        if filename is None:
            filename = os.path.basename(path)
        with open(path, "rb") as f:
            data = f.read()
        return cls(data, filename=filename, chunk_size=chunk_size)

    async def read(self, chunk_size: int) -> AsyncGenerator[bytes, None]:
        buffer = io.BytesIO(self.data)
        chunk = buffer.read(chunk_size)
        while chunk:
            yield chunk
            chunk = buffer.read(chunk_size)


class FSInputFile(InputFile):
    def __init__(
        self,
        path: Union[str, Path],
        filename: Optional[str] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        if filename is None:
            filename = os.path.basename(path)
        super().__init__(filename=filename, chunk_size=chunk_size)

        self.path = path

    async def read(self, chunk_size: int) -> AsyncGenerator[bytes, None]:
        async with aiofiles.open(self.path, "rb") as f:
            chunk = await f.read(chunk_size)
            while chunk:
                yield chunk
                chunk = await f.read(chunk_size)
