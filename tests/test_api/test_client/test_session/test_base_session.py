import datetime
import json
from typing import Any, AsyncContextManager, AsyncGenerator, Dict, Optional
from unittest.mock import AsyncMock, patch

import pytest
from pytz import utc

from aiogram import Bot
from aiogram.client.default import Default, DefaultBotProperties
from aiogram.client.session.base import BaseSession, TelegramType
from aiogram.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.enums import ChatType, ParseMode, TopicIconColor
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
from aiogram.types import UNSET_PARSE_MODE, LinkPreviewOptions, User
from aiogram.types.base import UNSET_DISABLE_WEB_PAGE_PREVIEW, UNSET_PROTECT_CONTENT
from tests.mocked_bot import MockedBot


class CustomSession(BaseSession):
    async def close(self):
        pass

    async def make_request(
        self,
        token: str,
        method: TelegramMethod[TelegramType],
        timeout: Optional[int] = UNSET_PARSE_MODE,
    ) -> None:  # type: ignore
        assert isinstance(token, str)
        assert isinstance(method, TelegramMethod)

    async def stream_content(
        self,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        assert isinstance(url, str)
        assert isinstance(timeout, int)
        assert isinstance(chunk_size, int)
        assert isinstance(raise_for_status, bool)
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

    @pytest.mark.parametrize(
        "value,result",
        [
            [None, None],
            ["text", "text"],
            [ChatType.PRIVATE, "private"],
            [TopicIconColor.RED, "16478047"],
            [42, "42"],
            [True, "true"],
            [["test"], '["test"]'],
            [["test", ["test"]], '["test", ["test"]]'],
            [[{"test": "pass", "spam": None}], '[{"test": "pass"}]'],
            [{"test": "pass", "number": 42, "spam": None}, '{"test": "pass", "number": 42}'],
            [{"foo": {"test": "pass", "spam": None}}, '{"foo": {"test": "pass"}}'],
            [
                datetime.datetime(
                    year=2017, month=5, day=17, hour=4, minute=11, second=42, tzinfo=utc
                ),
                "1494994302",
            ],
            [
                {"link_preview": LinkPreviewOptions(is_disabled=True)},
                '{"link_preview": {"is_disabled": true}}',
            ],
        ],
    )
    def test_prepare_value(self, value: Any, result: str, bot: MockedBot):
        session = CustomSession()

        assert session.prepare_value(value, bot=bot, files={}) == result

    def test_prepare_value_timedelta(self, bot: MockedBot):
        session = CustomSession()

        value = session.prepare_value(datetime.timedelta(minutes=2), bot=bot, files={})
        assert isinstance(value, str)

    def test_prepare_value_defaults_replace(self):
        bot = MockedBot(
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                protect_content=True,
                link_preview_is_disabled=True,
            )
        )
        assert bot.session.prepare_value(Default("parse_mode"), bot=bot, files={}) == "HTML"
        assert (
            bot.session.prepare_value(Default("link_preview_is_disabled"), bot=bot, files={})
            == "true"
        )
        assert bot.session.prepare_value(Default("protect_content"), bot=bot, files={}) == "true"

    def test_prepare_value_defaults_unset(self):
        bot = MockedBot()
        assert bot.session.prepare_value(UNSET_PARSE_MODE, bot=bot, files={}) is None
        assert bot.session.prepare_value(UNSET_DISABLE_WEB_PAGE_PREVIEW, bot=bot, files={}) is None
        assert bot.session.prepare_value(UNSET_PROTECT_CONTENT, bot=bot, files={}) is None

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
        bot = MockedBot()
        method = DeleteMessage(chat_id=42, message_id=42)
        if error is None:
            session.check_response(
                bot=bot,
                method=method,
                status_code=status_code,
                content=content,
            )
        else:
            with pytest.raises(error) as exc_info:
                session.check_response(
                    bot=bot,
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
        bot = MockedBot()
        method = DeleteMessage(chat_id=42, message_id=42)

        with pytest.raises(ClientDecodeError, match="JSONDecodeError"):
            session.check_response(
                bot=bot,
                method=method,
                status_code=200,
                content="is not a JSON object",
            )

    def test_check_response_validation_error(self):
        session = CustomSession()
        bot = MockedBot()
        method = DeleteMessage(chat_id=42, message_id=42)

        with pytest.raises(ClientDecodeError, match="ValidationError"):
            session.check_response(
                bot=bot,
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
            "https://www.python.org/static/img/python-logo.png",
            headers={},
            timeout=5,
            chunk_size=65536,
            raise_for_status=True,
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
