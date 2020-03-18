from __future__ import annotations

from contextlib import asynccontextmanager
from typing import (
    Any,
    AsyncIterator,
    Optional,
    TypeVar,
)

from ...utils.mixins import (
    ContextInstance,
    ContextInstanceMixin,
)
from ...utils.token import extract_bot_id, validate_token
from ..methods import TelegramMethod
from .session.aiohttp import AiohttpSession
from .session.base import BaseSession

T = TypeVar("T")


class BaseBot(ContextInstanceMixin[ContextInstance]):
    """
    Base class for bots
    """

    def __init__(
        self, token: str, session: Optional[BaseSession] = None, parse_mode: Optional[str] = None
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
    async def context(self, auto_close: bool = True) -> AsyncIterator["BaseBot[ContextInstance]"]:
        """
        Generate bot context

        :param auto_close:
        :return:
        """
        # TODO: because set_current expects Bot, not BaseBot — this check fails
        token = self.set_current(self)  # type: ignore
        try:
            yield self
        finally:
            if auto_close:
                await self.close()
            self.reset_current(token)

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
