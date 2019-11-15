import abc
import asyncio
import datetime
import json
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from pydantic.dataclasses import dataclass

from aiogram.api.methods import Response, TelegramMethod

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


class BaseSession(abc.ABC):
    def __init__(
        self,
        api: TelegramAPIServer = PRODUCTION,
        json_loads: Optional[Callable] = None,
        json_dumps: Optional[Callable] = None,
    ):
        if json_loads is None:
            json_loads = json.loads
        if json_dumps is None:
            json_dumps = json.dumps

        self.api = api
        self.json_loads = json_loads
        self.json_dumps = json_dumps

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

    def prepare_value(self, value: Any) -> Union[str, int, bool]:
        if isinstance(value, str):
            return value
        if isinstance(value, (list, dict)):
            return self.json_dumps(self.clean_json(value))
        if isinstance(value, datetime.timedelta):
            now = datetime.datetime.now()
            return int((now + value).timestamp())
        if isinstance(value, datetime.datetime):
            return round(value.timestamp())
        else:
            return str(value)

    def clean_json(self, value: Union[List, Dict]):
        if isinstance(value, list):
            return [self.clean_json(v) for v in value if v is not None]
        elif isinstance(value, dict):
            return {k: self.clean_json(v) for k, v in value.items() if v is not None}
        return value
