from __future__ import annotations

import io
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    AsyncIterator,
    Dict,
    Optional,
    Union,
)

import aiofiles

if TYPE_CHECKING:
    from aiogram.client.bot import Bot

DEFAULT_CHUNK_SIZE = 64 * 1024  # 64 kb


class InputFile(ABC):
    """
    This object represents the contents of a file to be uploaded. Must be posted using multipart/form-data in the usual way that files are uploaded via the browser.

    Source: https://core.telegram.org/bots/api#inputfile
    """

    def __init__(self, filename: Optional[str] = None, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        Base class for input files. Should not be used directly.
        Look at :class:`BufferedInputFile`, :class:`FSInputFile` :class:`URLInputFile`

        :param filename: name of the given file
        :param chunk_size: reader chunks size
        """
        self.filename = filename
        self.chunk_size = chunk_size

    @abstractmethod
    async def read(self, chunk_size: int) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        yield b""

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self.read(self.chunk_size):
            yield chunk


class BufferedInputFile(InputFile):
    def __init__(self, file: bytes, filename: str, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        Represents object for uploading files from filesystem

        :param file: Bytes
        :param filename: Filename to be propagated to telegram.
        :param chunk_size: Uploading chunk size
        """
        super().__init__(filename=filename, chunk_size=chunk_size)

        self.data = file

    @classmethod
    def from_file(
        cls,
        path: Union[str, Path],
        filename: Optional[str] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> BufferedInputFile:
        """
        Create buffer from file

        :param path: Path to file
        :param filename: Filename to be propagated to telegram.
            By default, will be parsed from path
        :param chunk_size: Uploading chunk size
        :return: instance of :obj:`BufferedInputFile`
        """
        if filename is None:
            filename = os.path.basename(path)
        with open(path, "rb") as f:
            data = f.read()
        return cls(data, filename=filename, chunk_size=chunk_size)

    async def read(self, chunk_size: int) -> AsyncGenerator[bytes, None]:
        buffer = io.BytesIO(self.data)
        while chunk := buffer.read(chunk_size):
            yield chunk


class FSInputFile(InputFile):
    def __init__(
        self,
        path: Union[str, Path],
        filename: Optional[str] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        """
        Represents object for uploading files from filesystem

        :param path: Path to file
        :param filename: Filename to be propagated to telegram.
            By default, will be parsed from path
        :param chunk_size: Uploading chunk size
        """
        if filename is None:
            filename = os.path.basename(path)
        super().__init__(filename=filename, chunk_size=chunk_size)

        self.path = path

    async def read(self, chunk_size: int) -> AsyncGenerator[bytes, None]:
        async with aiofiles.open(self.path, "rb") as f:
            while chunk := await f.read(chunk_size):
                yield chunk


class URLInputFile(InputFile):
    def __init__(
        self,
        url: str,
        bot: "Bot",
        headers: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        timeout: int = 30,
    ):
        """
        Represents object for streaming files from internet

        :param url: URL in internet
        :param headers: HTTP Headers
        :param filename: Filename to be propagated to telegram.
        :param chunk_size: Uploading chunk size
        :param timeout: Timeout for downloading
        :param bot: Bot instance to use HTTP session from.
                    If not specified, will be used current bot from context.
        """
        super().__init__(filename=filename, chunk_size=chunk_size)
        if headers is None:
            headers = {}

        self.url = url
        self.headers = headers
        self.timeout = timeout
        self.bot = bot

    async def read(self, chunk_size: int) -> AsyncGenerator[bytes, None]:
        stream = self.bot.session.stream_content(
            url=self.url,
            headers=self.headers,
            timeout=self.timeout,
            chunk_size=self.chunk_size,
            raise_for_status=True,
        )

        async for chunk in stream:
            yield chunk
