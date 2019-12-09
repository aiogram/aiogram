from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Optional, TypeVar

from ...utils.mixins import ContextInstanceMixin, DataMixin
from ...utils.token import extract_bot_id, validate_token
from ..methods import TelegramMethod
from .session.aiohttp import AiohttpSession
from .session.base import BaseSession

T = TypeVar("T")


class BaseBot(ContextInstanceMixin, DataMixin):
    def __init__(self, token: str, session: BaseSession = None, parse_mode: Optional[str] = None):
        validate_token(token)

        if session is None:
            session = AiohttpSession()

        self.session = session
        self.parse_mode = parse_mode
        self.__token = token

    @property
    def id(self):
        return extract_bot_id(self.__token)

    async def emit(self, method: TelegramMethod[T]) -> T:
        return await self.session.make_request(self.__token, method)

    async def close(self):
        await self.session.close()

    @asynccontextmanager
    async def context(self, auto_close: bool = True):
        token = self.set_current(self)
        try:
            yield self
        finally:
            if auto_close:
                await self.close()
            self.reset_current(token)

    def __hash__(self):
        return hash(self.__token)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BaseBot):
            return False
        return hash(self) == hash(other)
