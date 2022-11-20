import datetime
import json
from typing import AsyncContextManager, AsyncGenerator, Optional
from unittest.mock import AsyncMock, patch

import pytest

from aiogram import Bot
from aiogram.client.session.base import BaseSession, TelegramType
from aiogram.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.enums import ChatType, TopicIconColor
from aiogram.exceptions import (
    ClientDecodeError,
    RestartingTelegram,
    TelegramAPIError,
    TelegramBadRequest,
    TelegramConflictError,
    TelegramEntityTooLarge,
    TelegramForbiddenError,
    TelegramMigrateToChat,
    TelegramNotFound,
    TelegramRetryAfter,
    TelegramServerError,
    TelegramUnauthorizedError,
)
from aiogram.methods import DeleteMessage, GetMe, TelegramMethod
from aiogram.types import UNSET, User
from tests.mocked_bot import MockedBot

pytestmark = pytest.mark.asyncio


class CustomSession(BaseSession):
    async def close(self):
        pass

    async def make_request(
        self, token: str, method: TelegramMethod[TelegramType], timeout: Optional[int] = UNSET
    ) -> None:  # type: ignore
        assert isinstance(token, str)
        assert isinstance(method, TelegramMethod)

    async def stream_content(
        self, url: str, timeout: int, chunk_size: int
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        assert isinstance(url, str)
        assert isinstance(timeout, int)
        assert isinstance(chunk_size, int)
        yield b"\f" * 10


class TestBaseSession:
    def test_init_api(self):
        session = CustomSession()
        assert session.api == PRODUCTION

    def test_default_props(self):
        session = CustomSession()
        assert session.api == PRODUCTION
        assert session.json_loads == json.loads
        assert session.json_dumps == json.dumps

        def custom_loads(*_):
            return json.loads

        def custom_dumps(*_):
            return json.dumps

        session.json_dumps = custom_dumps
        assert session.json_dumps == custom_dumps
        session.json_loads = custom_loads
        assert session.json_loads == custom_loads

    def test_init_custom_api(self):
        api = TelegramAPIServer(
            base="http://example.com/{token}/{method}",
            file="http://example.com/{token}/file/{path}",
        )
        session = CustomSession()
        session.api = api
        assert session.api == api
        assert "example.com" in session.api.base

    def test_prepare_value(self):
        session = CustomSession()

        now = datetime.datetime.now()

        assert session.prepare_value("text") == "text"
        assert session.prepare_value(["test"]) == '["test"]'
        assert session.prepare_value({"test": "ok"}) == '{"test": "ok"}'
        assert session.prepare_value(now) == str(round(now.timestamp()))
        assert isinstance(session.prepare_value(datetime.timedelta(minutes=2)), str)
        assert session.prepare_value(42) == "42"
        assert session.prepare_value(ChatType.PRIVATE) == "private"
        assert session.prepare_value(TopicIconColor.RED) == "16478047"

    def test_clean_json(self):
        session = CustomSession()

        cleaned_dict = session.clean_json({"key": "value", "null": None})
        assert "key" in cleaned_dict
        assert "null" not in cleaned_dict

        cleaned_list = session.clean_json(["kaboom", 42, None])
        assert len(cleaned_list) == 2
        assert 42 in cleaned_list
        assert None not in cleaned_list
        assert cleaned_list[0] == "kaboom"

    def test_clean_json_with_nested_json(self):
        session = CustomSession()

        cleaned = session.clean_json(
            {
                "key": "value",
                "null": None,
                "nested_list": ["kaboom", 42, None],
                "nested_dict": {"key": "value", "null": None},
            }
        )

        assert len(cleaned) == 3
        assert "null" not in cleaned

        assert isinstance(cleaned["nested_list"], list)
        assert cleaned["nested_list"] == ["kaboom", 42]

        assert isinstance(cleaned["nested_dict"], dict)
        assert cleaned["nested_dict"] == {"key": "value"}

    def test_clean_json_not_json(self):
        session = CustomSession()

        assert session.clean_json(42) == 42

    @pytest.mark.parametrize(
        "status_code,content,error",
        [
            [200, '{"ok":true,"result":true}', None],
            [400, '{"ok":false,"description":"test"}', TelegramBadRequest],
            [
                400,
                '{"ok":false,"description":"test", "parameters": {"retry_after": 1}}',
                TelegramRetryAfter,
            ],
            [
                400,
                '{"ok":false,"description":"test", "parameters": {"migrate_to_chat_id": -42}}',
                TelegramMigrateToChat,
            ],
            [404, '{"ok":false,"description":"test"}', TelegramNotFound],
            [401, '{"ok":false,"description":"test"}', TelegramUnauthorizedError],
            [403, '{"ok":false,"description":"test"}', TelegramForbiddenError],
            [409, '{"ok":false,"description":"test"}', TelegramConflictError],
            [413, '{"ok":false,"description":"test"}', TelegramEntityTooLarge],
            [500, '{"ok":false,"description":"restarting"}', RestartingTelegram],
            [500, '{"ok":false,"description":"test"}', TelegramServerError],
            [502, '{"ok":false,"description":"test"}', TelegramServerError],
            [499, '{"ok":false,"description":"test"}', TelegramAPIError],
            [499, '{"ok":false,"description":"test"}', TelegramAPIError],
        ],
    )
    def test_check_response(self, status_code, content, error):
        session = CustomSession()
        method = DeleteMessage(chat_id=42, message_id=42)
        if error is None:
            session.check_response(
                method=method,
                status_code=status_code,
                content=content,
            )
        else:
            with pytest.raises(error) as exc_info:
                session.check_response(
                    method=method,
                    status_code=status_code,
                    content=content,
                )
            error: TelegramAPIError = exc_info.value
            string = str(error)
            if error.url:
                assert error.url in string

    def test_check_response_json_decode_error(self):
        session = CustomSession()
        method = DeleteMessage(chat_id=42, message_id=42)

        with pytest.raises(ClientDecodeError, match="JSONDecodeError"):
            session.check_response(
                method=method,
                status_code=200,
                content="is not a JSON object",
            )

    def test_check_response_validation_error(self):
        session = CustomSession()
        method = DeleteMessage(chat_id=42, message_id=42)

        with pytest.raises(ClientDecodeError, match="ValidationError"):
            session.check_response(
                method=method,
                status_code=200,
                content='{"ok": "test"}',
            )

    async def test_make_request(self):
        session = CustomSession()

        assert await session.make_request("42:TEST", GetMe()) is None

    async def test_stream_content(self):
        session = CustomSession()
        stream = session.stream_content(
            "https://www.python.org/static/img/python-logo.png", timeout=5, chunk_size=65536
        )
        assert isinstance(stream, AsyncGenerator)

        async for chunk in stream:
            assert isinstance(chunk, bytes)

    async def test_context_manager(self):
        session = CustomSession()
        assert isinstance(session, AsyncContextManager)

        with patch(
            "tests.test_api.test_client.test_session.test_base_session.CustomSession.close",
            new_callable=AsyncMock,
        ) as mocked_close:
            async with session as ctx:
                assert session == ctx
            mocked_close.assert_awaited_once()

    def test_add_middleware(self):
        async def my_middleware(bot, method, make_request):
            return await make_request(bot, method)

        session = CustomSession()
        assert not session.middleware._middlewares

        session.middleware(my_middleware)
        assert my_middleware in session.middleware
        assert len(session.middleware) == 1

    async def test_use_middleware(self, bot: MockedBot):
        flag_before = False
        flag_after = False

        @bot.session.middleware
        async def my_middleware(make_request, b, method):
            nonlocal flag_before, flag_after
            flag_before = True
            try:
                assert isinstance(b, Bot)
                assert isinstance(method, TelegramMethod)

                return await make_request(b, method)
            finally:
                flag_after = True

        bot.add_result_for(GetMe, ok=True, result=User(id=42, is_bot=True, first_name="Test"))
        assert await bot.get_me()
        assert flag_before
        assert flag_after
