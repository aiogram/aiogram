import datetime
from typing import AsyncContextManager, AsyncGenerator

import pytest

from aiogram.api.client.session.base import BaseSession, T
from aiogram.api.client.telegram import PRODUCTION, TelegramAPIServer
from aiogram.api.methods import GetMe, Response, TelegramMethod
from aiogram.utils.mixins import DataMixin

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock, patch  # type: ignore


class CustomSession(BaseSession):
    async def close(self):
        pass

    async def make_request(self, token: str, method: TelegramMethod[T]) -> None:  # type: ignore
        assert isinstance(token, str)
        assert isinstance(method, TelegramMethod)

    async def stream_content(
        self, url: str, timeout: int, chunk_size: int
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover
        assert isinstance(url, str)
        assert isinstance(timeout, int)
        assert isinstance(chunk_size, int)
        yield b"\f" * 10


class TestBaseSession(DataMixin):
    def test_init_api(self):
        session = CustomSession()
        assert session.api == PRODUCTION

    def test_init_custom_api(self):
        api = TelegramAPIServer(
            base="http://example.com/{token}/{method}",
            file="http://example.com/{token}/file/{path{",
        )
        session = CustomSession(api=api)
        assert session.api == api

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

    def test_raise_for_status(self):
        session = CustomSession()

        session.raise_for_status(Response[bool](ok=True, result=True))
        with pytest.raises(Exception):
            session.raise_for_status(Response[bool](ok=False, description="Error", error_code=400))

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
            mocked_close.awaited_once()
