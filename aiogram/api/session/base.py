import abc
import asyncio
from typing import Generic, TypeVar

from aiogram.api.methods import Response, TelegramMethod
from pydantic.dataclasses import dataclass

T = TypeVar("T")


@dataclass
class TelegramAPIServer:
    base: str
    file: str

    def api_url(self, token: str, method: str) -> str:
        return self.base.format(token=token, method=method)

    def file_url(self, token: str, path: str) -> str:
        return self.file.format(token=token, path=path)


PRODUCTION = TelegramAPIServer(
    base="https://api.telegram.org/bot{token}/{method}",
    file="https://api.telegram.org/file/bot{token}/{path}",
)


class BaseSession(abc.ABC, Generic[T]):
    def __init__(self, api: TelegramAPIServer = PRODUCTION):
        self.api = api

    def raise_for_status(self, response: Response[T]):
        if response.ok:
            return
        raise Exception(response.description)

    @abc.abstractmethod
    async def close(self):
        pass

    @abc.abstractmethod
    async def make_request(self, token: str, method: TelegramMethod[T]) -> T:
        pass

    def __del__(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is None or loop.is_closed():
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.close())
            return
        loop.create_task(self.close())
