import re
from typing import AsyncContextManager, AsyncGenerator

import httpx
import pytest
import respx
from pip._vendor.packaging.version import Version
from respx import HTTPXMock

from aiogram.api.client.session.httpx import HttpxSession
from aiogram.api.methods import Request, TelegramMethod
from aiogram.api.types import InputFile

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock, patch  # type: ignore


@pytest.fixture
def httpx_mock():
    with respx.mock() as httpx_mock:
        yield httpx_mock


class BareInputFile(InputFile):
    async def read(self, chunk_size: int):
        yield b""


class TestHttpxSession:
    @pytest.mark.asyncio
    async def test_create_session(self):
        session = HttpxSession()

        assert session._client is None
        httpx_session = await session.create_session()
        assert session._client is not None
        assert isinstance(httpx_session, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_close_session(self):
        session = HttpxSession()
        await session.create_session()

        with patch("httpx.AsyncClient.aclose", new=CoroutineMock()) as mocked_close:
            await session.close()
            mocked_close.assert_called_once()

    def test_build_form_data_with_data_only(self):
        request = Request(
            method="method",
            data={
                "str": "value",
                "int": 42,
                "bool": True,
                "null": None,
                "list": ["foo"],
                "dict": {"bar": "baz"},
            },
        )

        session = HttpxSession()
        form, files = session.build_form_data(request)

        fields = list(form.keys()) + list(files.keys())
        assert len(fields) == 5
        assert all(isinstance(field, str) for field in fields)
        assert "null" not in fields

    def test_build_form_data_with_files(self):
        request = Request(
            method="method",
            data={"key": "value"},
            files={"document": BareInputFile(filename="file.txt")},
        )

        session = HttpxSession()
        form, files = session.build_form_data(request)

        assert len(form) + len(files) == 2
        assert "document" in files
        assert files["document"][1] == "file.txt"
        assert isinstance(files["document"][0], BareInputFile)

    @pytest.mark.asyncio
    async def test_make_request(self, httpx_mock: HTTPXMock):
        httpx_mock.post(
            url=re.compile(r".*/bot42:TEST/method"),
            status_code=200,
            content='{"ok": true, "result": 42}',
            content_type="application/json",
        )

        session = HttpxSession()

        class TestMethod(TelegramMethod[int]):
            __returning__ = int

            def build_request(self) -> Request:
                return Request(method="method", data={})

        call = TestMethod()
        with patch(
            "aiogram.api.client.session.base.BaseSession.raise_for_status"
        ) as patched_raise_for_status:
            result = await session.make_request("42:TEST", call)
            assert isinstance(result, int)
            assert result == 42

            assert patched_raise_for_status.called_once()

    # Update right Version if httpx still didn't implement it
    # https://github.com/encode/httpx/issues/394
    @pytest.mark.skipif(
        Version(httpx.__version__) <= Version("0.12"),
        reason="old httpx doesn't support chunk_size",
    )
    @pytest.mark.asyncio
    async def test_stream_content(self, httpx_mock: HTTPXMock):

        httpx_mock.get(
            url=re.compile(".*"), status_code=200, content=b"\f" * 10,
        )

        session = HttpxSession()
        stream = session.stream_content(
            "https://www.python.org/static/img/python-logo.png", timeout=5, chunk_size=1
        )
        assert isinstance(stream, AsyncGenerator)

        size = 0
        async for chunk in stream:
            assert isinstance(chunk, bytes)
            chunk_size = len(chunk)
            assert chunk_size == 1
            size += chunk_size
        assert size == 10

    @pytest.mark.asyncio
    async def test_context_manager(self):
        session = HttpxSession()
        assert isinstance(session, AsyncContextManager)

        with patch(
            "aiogram.api.client.session.httpx.HttpxSession.create_session",
            new_callable=CoroutineMock,
        ) as mocked_create_session, patch(
            "aiogram.api.client.session.httpx.HttpxSession.close", new_callable=CoroutineMock
        ) as mocked_close:
            async with session as ctx:
                assert session == ctx
            mocked_close.awaited_once()
            mocked_create_session.awaited_once()
