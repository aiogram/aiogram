from collections import deque
from typing import Optional

from aiogram import Bot
from aiogram.api.client.session.base import BaseSession
from aiogram.api.methods import TelegramMethod
from aiogram.api.methods.base import T, Request, Response


class MockedSession(BaseSession):
    def __init__(self):
        super(MockedSession, self).__init__()
        self.responses = deque()
        self.requests = deque()

    def add_result(self, response: Response) -> Response:
        self.responses.append(response)
        return response

    def get_request(self) -> Request:
        return self.requests.pop()

    async def close(self):
        pass

    async def make_request(self, token: str, method: TelegramMethod[T]) -> T:
        self.requests.append(method.build_request())
        response: Response = self.responses.pop()
        self.raise_for_status(response)
        return response.result


class MockedBot(Bot):
    def __init__(self):
        super(MockedBot, self).__init__("TOKEN", session=MockedSession())

    def add_result_for(
        self,
        method,
        ok: bool,
        result: Optional[T] = None,
        description: Optional[str] = None,
        error_code: Optional[int] = None,
        migrate_to_chat_id: Optional[int] = None,
        retry_after: Optional[int] = None,
    ) -> Response[T]:
        response = Response[method.__returning__](
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
