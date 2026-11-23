import json
from collections import deque
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic

from aiogram import Bot
from aiogram.client.session.base import DEFAULT_DOWNLOAD_TIMEOUT, BaseSession, DownloadTimeout
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from aiogram.types import BotFullInfo


@dataclass
class MockedResponse(Generic[TelegramType]):
    """Plain response record; turned into the wire envelope only in ``make_request``."""

    ok: bool
    result: TelegramType | None = None
    description: str | None = None
    error_code: int = 200
    migrate_to_chat_id: int | None = None
    retry_after: int | None = None


def _wire_default(value: Any) -> Any:
    # The only line that depends on the model layer. Switch to `value.to_dict()` when C-13 moves
    # `aiogram.types` to the native model layer.
    return value.model_dump(mode="json")


class MockedSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.responses: deque[MockedResponse[Any]] = deque()
        self.requests: deque[TelegramMethod[Any]] = deque()
        self.closed = True

    def add_result(self, response: MockedResponse[TelegramType]) -> MockedResponse[TelegramType]:
        self.responses.append(response)
        return response

    def get_request(self) -> TelegramMethod[Any]:
        return self.requests.pop()

    async def close(self):
        self.closed = True

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,
    ) -> TelegramType:
        self.closed = False
        self.requests.append(method)
        response = self.responses.pop()
        content = json.dumps(
            {
                "ok": response.ok,
                "result": response.result,
                "description": response.description,
                "error_code": response.error_code,
                "parameters": {
                    "migrate_to_chat_id": response.migrate_to_chat_id,
                    "retry_after": response.retry_after,
                },
            },
            default=_wire_default,
        )
        # The public response-check path; D-11 replaces this call with its decode entry.
        self.check_response(
            bot=bot,
            method=method,
            status_code=response.error_code,
            content=content,
        )
        return response.result  # type: ignore[return-value]

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: DownloadTimeout | float = DEFAULT_DOWNLOAD_TIMEOUT,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        yield b""


class MockedBot(Bot):
    if TYPE_CHECKING:
        session: MockedSession

    def __init__(self, **kwargs):
        super().__init__(token=kwargs.pop("token", "42:TEST"), session=MockedSession(), **kwargs)
        self._me = bot_full_info(id=self.id, first_name="FirstName", username="tbot")

    def add_result_for(
        self,
        method: type[TelegramMethod[TelegramType]],
        ok: bool,
        result: TelegramType = None,
        description: str | None = None,
        error_code: int = 200,
        migrate_to_chat_id: int | None = None,
        retry_after: int | None = None,
    ) -> MockedResponse[TelegramType]:
        return self.session.add_result(
            MockedResponse(
                ok=ok,
                result=result,
                description=description,
                error_code=error_code,
                migrate_to_chat_id=migrate_to_chat_id,
                retry_after=retry_after,
            )
        )

    def get_request(self) -> TelegramMethod[TelegramType]:
        return self.session.get_request()


def bot_full_info(**kwargs: Any) -> BotFullInfo:
    """A getMe result: all the required BotFullInfo flags are False unless overridden."""
    # Model-layer dependency like `_wire_default`: C-13 switches `model_fields` with it.
    flags = {
        name: False
        for name, field in BotFullInfo.model_fields.items()
        if field.annotation is bool and name != "is_bot"
    }
    return BotFullInfo(**{"id": 42, "is_bot": True, "first_name": "Test", **flags, **kwargs})
