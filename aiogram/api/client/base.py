from typing import TypeVar

from ...utils.mixins import ContextInstanceMixin
from ..methods import TelegramMethod
from .session.aiohttp import AiohttpSession
from .session.base import BaseSession

T = TypeVar("T")


class BaseBot(ContextInstanceMixin):
    def __init__(self, token: str, session: BaseSession = None):
        if session is None:
            session = AiohttpSession()
        self.session = session
        self.token = token

    async def emit(self, method: TelegramMethod[T]) -> T:
        return await self.session.make_request(self.token, method)

    async def close(self):
        await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
