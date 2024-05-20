from __future__ import annotations

import io
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Optional, Union

import aiofiles
from pydantic import BaseModel, Field, model_validator

from aiogram.client.context_controller import BotContextController

if TYPE_CHECKING:
    from aiogram.client.bot import Bot

DEFAULT_CHUNK_SIZE = 64 * 1024  # 64 kb


class InputFile(BaseModel):
    """
    Base class for input files.
    This object represents the contents of a file to be uploaded. Must be posted using multipart/form-data in the usual way that files are uploaded via the browser.
    Should not be used directly. Look at :class:`BufferedInputFile`, :class:`FSInputFile` :class:`URLInputFile`

    Source: https://core.telegram.org/bots/api#inputfile
    """

    filename: Optional[str] = None
    """Name of the given file"""
    chunk_size: int = DEFAULT_CHUNK_SIZE
    """Reader chunks size"""

    def __init__(self, filename: Optional[str] = None, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        Backward compatibility (positional arguments)
        """
        super().__init__(
            filename=filename,
            chunk_size=chunk_size,
        )

    @abstractmethod
    async def read(self, bot: "Bot") -> AsyncGenerator[bytes, None]:  # pragma: no cover
        yield b""


class BufferedInputFile(InputFile):
    """
    Represents object for uploading files from filesystem
    """

    data: bytes
    """File bytes"""
    filename: str
    """Filename to be propagated to telegram"""

    def __init__(self, file: bytes, filename: str, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        Backward compatibility (positional arguments and old naming)
        """
        super(InputFile, self).__init__(
            data=file,
            filename=filename,
            chunk_size=chunk_size,
        )

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
        path = Path(path)
        filename = filename or path.name
        file = path.read_bytes()
        return cls(file=file, filename=filename, chunk_size=chunk_size)

    async def read(self, bot: "Bot") -> AsyncGenerator[bytes, None]:
        buffer = io.BytesIO(self.data)
        while chunk := buffer.read(self.chunk_size):
            yield chunk


class FSInputFile(InputFile):
    """
    Represents object for uploading files from filesystem
    """

    path: Path
    """Path to file"""
    filename: str = ""  # set it from path after validation
    """Filename to be propagated to telegram"""

    def __init__(
        self,
        path: Union[str, Path],
        filename: Optional[str] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        """
        Backward compatibility (positional arguments)
        """
        super(InputFile, self).__init__(
            path=Path(path),
            filename=filename or "",
            chunk_size=chunk_size,
        )

    @model_validator(mode="after")
    def filename_from_path(self):
        self.filename = self.filename or Path(self.path).name

    async def read(self, bot: "Bot") -> AsyncGenerator[bytes, None]:
        async with aiofiles.open(self.path, "rb") as f:
            while chunk := await f.read(self.chunk_size):
                yield chunk


class URLInputFile(BotContextController, InputFile):
    """
    Represents object for streaming files from internet
    """

    url: str
    """URL in internet"""
    headers: Dict[str, Any] = Field(default_factory=dict)
    """HTTP Headers"""
    timeout: int = 30
    """Timeout for downloading"""

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        timeout: int = 30,
        bot: Optional["Bot"] = None,
    ):
        """
        Backward compatibility (positional arguments and bot context)
        """
        super(InputFile, self).__init__(
            url=url,
            headers=headers or {},
            timeout=timeout,
            filename=filename,
            chunk_size=chunk_size,
        )

        self._bot = bot

    async def read(self, bot: Optional["Bot"] = None) -> AsyncGenerator[bytes, None]:
        bot = self.bot or bot  # FIXME: invalid order suspected
        stream = bot.session.stream_content(
            url=self.url,
            headers=self.headers,
            timeout=self.timeout,
            chunk_size=self.chunk_size,
            raise_for_status=True,
        )

        async for chunk in stream:
            yield chunk
