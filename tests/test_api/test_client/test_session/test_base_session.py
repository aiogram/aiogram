import datetime
import json
from typing import AsyncContextManager, AsyncGenerator, Optional

import pytest

from aiogram.client.session.base import BaseSession, TelegramType
from aiogram.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.methods import DeleteMessage, GetMe, Response, TelegramMethod
from aiogram.types import UNSET

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock  # type: ignore
    from unittest.mock import patch


class CustomSession(BaseSession):
    async def close(self):
        pass

    async def make_request(self, token: str, method: TelegramMethod[TelegramType], timeout: Optional[int] = UNSET) -> None:  # type: ignore
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

    def test_timeout(self):
        session = CustomSession()
        assert session.timeout == session.default_timeout == CustomSession.default_timeout

        session.default_timeout = float(65.0_0)  # mypy will complain
        assert session.timeout != session.default_timeout

        CustomSession.default_timeout = float(68.0_0)
        assert session.timeout == CustomSession.default_timeout

        session.timeout = float(71.0_0)
        assert session.timeout != session.default_timeout
        del session.timeout
        CustomSession.default_timeout = session.default_timeout + 100
        assert (
            session.timeout != BaseSession.default_timeout
            and session.timeout == CustomSession.default_timeout
        )

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

    def check_response(self):
        session = CustomSession()

        session.check_response(
            method=DeleteMessage(chat_id=42, message_id=42),
            status_code=200,
            content='{"ok":true,"result":true}',
        )
        with pytest.raises(Exception):
            session.check_response(
                method=DeleteMessage(chat_id=42, message_id=42),
                status_code=400,
                content='{"ok":false,"description":"test"}',
            )

    @pytest.mark.asyncio
    async def test_make_request(self):
        session = CustomSession()

        assert await session.make_request("42:TEST", GetMe()) is None

    @pytest.mark.asyncio
    async def test_stream_content(self):
        session = CustomSession()
        stream = session.stream_content(
            "https://www.python.org/static/img/python-logo.png", timeout=5, chunk_size=65536
        )
        assert isinstance(stream, AsyncGenerator)

        async for chunk in stream:
            assert isinstance(chunk, bytes)

    @pytest.mark.asyncio
    async def test_context_manager(self):
        session = CustomSession()
        assert isinstance(session, AsyncContextManager)

        with patch(
            "tests.test_api.test_client.test_session.test_base_session.CustomSession.close",
            new_callable=CoroutineMock,
        ) as mocked_close:
            async with session as ctx:
                assert session == ctx
            mocked_close.assert_awaited_once()
