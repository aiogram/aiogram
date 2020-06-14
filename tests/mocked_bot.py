from collections import deque
from typing import TYPE_CHECKING, AsyncGenerator, Deque, Optional, Type

from aiogram import Bot
from aiogram.api.client.session.base import BaseSession
from aiogram.api.methods import TelegramMethod
from aiogram.api.methods.base import Request, Response, T
from aiogram.api.types import UNSET


class MockedSession(BaseSession):
    def __init__(self):
        super(MockedSession, self).__init__()
        self.responses: Deque[Response[T]] = deque()
        self.requests: Deque[Request] = deque()

    def add_result(self, response: Response[T]) -> Response[T]:
        self.responses.append(response)
        return response

    def get_request(self) -> Request:
        return self.requests.pop()

    async def close(self):
        pass

    async def make_request(
        self, bot: Bot, method: TelegramMethod[T], timeout: Optional[int] = UNSET
    ) -> T:
        self.requests.append(method.build_request(bot))
        response: Response[T] = self.responses.pop()
        self.raise_for_status(response)
        return response.result  # type: ignore

    async def stream_content(
        self, url: str, timeout: int, chunk_size: int
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        yield b""


class MockedBot(Bot):
    if TYPE_CHECKING:
        session: MockedSession

    def __init__(self, **kwargs):
        super(MockedBot, self).__init__("42:TEST", session=MockedSession(), **kwargs)

    def add_result_for(
        self,
        method: Type[TelegramMethod[T]],
        ok: bool,
        result: T = None,
        description: Optional[str] = None,
        error_code: Optional[int] = None,
        migrate_to_chat_id: Optional[int] = None,
        retry_after: Optional[int] = None,
    ) -> Response[T]:
        response = Response[method.__returning__](  # type: ignore
            ok=ok,
            result=result,
            description=description,
            error_code=error_code,
            migrate_to_chat_id=migrate_to_chat_id,
            retry_after=retry_after,
        )
        self.session.add_result(response)
        return response

    def get_request(self) -> Request:
        return self.session.get_request()
