from __future__ import annotations

import io
import pathlib
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, BinaryIO, Optional, TypeVar, Union

import aiofiles

from ...utils.mixins import ContextInstanceMixin, DataMixin
from ...utils.token import extract_bot_id, validate_token
from ..methods import TelegramMethod
from .session.aiohttp import AiohttpSession
from .session.base import BaseSession

T = TypeVar("T")


class BaseBot(ContextInstanceMixin, DataMixin):
    """
    Base class for bots
    """

    def __init__(
        self, token: str, session: BaseSession = None, parse_mode: Optional[str] = None
    ) -> None:
        validate_token(token)

        if session is None:
            session = AiohttpSession()

        self.session = session
        self.parse_mode = parse_mode
        self.__token = token

    @property
    def id(self) -> int:
        """
        Get bot ID from token

        :return:
        """
        return extract_bot_id(self.__token)

    async def __call__(self, method: TelegramMethod[T]) -> T:
        """
        Call API method

        :param method:
        :return:
        """
        return await self.session.make_request(self.__token, method)

    async def close(self) -> None:
        """
        Close bot session
        """
        await self.session.close()

    @asynccontextmanager
    async def context(self, auto_close: bool = True):
        """
        Generate bot context

        :param auto_close:
        :return:
        """
        token = self.set_current(self)
        try:
            yield self
        finally:
            if auto_close:
                await self.close()
            self.reset_current(token)

    @staticmethod
    async def __download_file_binary_io(
        destination: BinaryIO, seek: bool, stream: AsyncGenerator[bytes, None]
    ) -> BinaryIO:
        async for chunk in stream:
            destination.write(chunk)
            destination.flush()
        if seek is True:
            destination.seek(0)
        return destination

    @staticmethod
    async def __download_file(
        destination: Union[str, pathlib.Path], stream: AsyncGenerator[bytes, None]
    ):
        async with aiofiles.open(destination, "wb") as f:
            async for chunk in stream:
                await f.write(chunk)

    async def download_file(
        self,
        file_path: str,
        destination: Optional[Union[BinaryIO, pathlib.Path, str]] = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        seek: bool = True,
    ) -> Optional[BinaryIO]:
        """
        Download file by file_path to destination.

        If you want to automatically create destination (:class:`io.BytesIO`) use default
        value of destination and handle result of this method.

        :param file_path: File path on Telegram server (You can get it from :obj:`aiogram.types.File`)
        :type file_path: str
        :param destination: Filename, file path or instance of :class:`io.IOBase`. For e.g. :class:`io.BytesIO`, defaults to None
        :type destination: Optional[Union[BinaryIO, pathlib.Path, str]]
        :param timeout: Total timeout in seconds, defaults to 30
        :type timeout: int
        :param chunk_size: File chunks size, defaults to 64 kb
        :type chunk_size: int
        :param seek: Go to start of file when downloading is finished. Used only for destination with :class:`typing.BinaryIO` type, defaults to True
        :type seek: bool
        """
        if destination is None:
            destination = io.BytesIO()

        url = self.get_file_url(file_path)
        stream = self.session.stream_content(url=url, timeout=timeout, chunk_size=chunk_size)

        if isinstance(destination, (str, pathlib.Path)):
            return await self.__download_file(destination=destination, stream=stream)
        else:
            return await self.__download_file_binary_io(
                destination=destination, seek=seek, stream=stream
            )

    def get_file_url(self, file_path: str) -> str:
        """
        Get file url

        Attention!!
        This method has security vulnerabilities for the reason that result
        contains bot's *access token* in open form. Use at your own risk!

        :param file_path: File path on Telegram server (You can get it from :obj:`aiogram.types.File`)
        :type file_path: str
        """
        return self.session.api.file_url(self.__token, file_path)

    def __hash__(self) -> int:
        """
        Get hash for the token

        :return:
        """
        return hash(self.__token)

    def __eq__(self, other: Any) -> bool:
        """
        Compare current bot with another bot instance

        :param other:
        :return:
        """
        if not isinstance(other, BaseBot):
            return False
        return hash(self) == hash(other)
