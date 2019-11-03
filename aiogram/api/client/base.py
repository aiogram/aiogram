from typing import TypeVar

from ..methods import TelegramMethod
from ..session.aiohttp import AiohttpSession
from ..session.base import BaseSession

T = TypeVar("T")


class BaseBot:
    def __init__(self, token: str, session: BaseSession = None):
        if session is None:
            session = AiohttpSession()
        self.session = session
        self.token = token

    async def emit(self, method: TelegramMethod[T]) -> T:
        return await self.session.make_request(self.token, method)
