import asyncio
import io
import sys
import warnings
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from aiogram import Bot
from aiogram.client.bot import DownloadStream
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.session.base import (
    DEFAULT_DOWNLOAD_TIMEOUT,
    LEGACY_DOWNLOAD_TIMEOUT,
    DownloadTimeout,
    _takes_download_timeout,
)
from aiogram.client.telegram import TelegramAPIServer
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import File, URLInputFile
from tests.test_api.test_client.test_session.test_base_session import CustomSession
from tests.token_safety import FAKE_TOKEN, assert_token_absent

FILE_PATH = "documents/file.bin"


class FileServer:
    """A local Bot API: `getFile` resolves any id to FILE_PATH, which `send` writes out."""

    def __init__(self, chunks: int, interval: float, stall: float = 0) -> None:
        self.chunks = chunks
        self.interval = interval
        self.stall = stall

    async def get_file(self, request: web.Request) -> web.Response:
        return web.json_response(
            {
                "ok": True,
                "result": {"file_id": "id", "file_unique_id": "u", "file_path": FILE_PATH},
            }
        )

    async def send(self, request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse()
        await response.prepare(request)
        try:
            for _ in range(self.chunks):
                await response.write(b"x")
                await asyncio.sleep(self.interval)
            await asyncio.sleep(self.stall)
            await response.write_eof()
        except (ConnectionResetError, asyncio.CancelledError):
            # the client went away early, which some tests do on purpose
            pass
        return response

    @asynccontextmanager
    async def bot(self, **session_kwargs: Any) -> AsyncIterator[Bot]:
        app = web.Application()
        app.router.add_post(f"/bot{FAKE_TOKEN}/getFile", self.get_file)
        app.router.add_get(f"/file/bot{FAKE_TOKEN}/{FILE_PATH}", self.send)
        async with TestServer(app) as server:
            api = TelegramAPIServer.from_base(str(server.make_url("")).rstrip("/"))
            async with Bot(FAKE_TOKEN, session=AiohttpSession(api=api)).context() as bot:
                yield bot


def acquired(bot: Bot) -> int:
    session = bot.session
    assert isinstance(session, AiohttpSession)
    assert session._session is not None
    return len(session._session.connector._acquired)  # type: ignore[union-attr]


async def settle() -> None:
    # The loop's asyncgen finalizer closes a dropped generator in a task of its own
    for _ in range(5):
        await asyncio.sleep(0)


class TestDownloadTimeout:
    def test_defaults(self):
        assert DEFAULT_DOWNLOAD_TIMEOUT == DownloadTimeout(connect=30, sock_read=60, total=None)

    def test_number_is_total(self):
        assert DownloadTimeout.of(5) == DownloadTimeout(connect=None, sock_read=None, total=5)
        timeout = DownloadTimeout(sock_read=1)
        assert DownloadTimeout.of(timeout) is timeout

    async def test_slow_transfer_has_no_total_cap(self):
        # 20 reads, each within `sock_read`, take longer than `sock_read` in total
        server = FileServer(chunks=20, interval=0.05)
        async with server.bot() as bot:
            result = await bot.download("id", timeout=DownloadTimeout(sock_read=0.5))
        assert result.read() == b"x" * 20

    async def test_stall_raises_without_token(self):
        server = FileServer(chunks=1, interval=0, stall=2)
        async with server.bot() as bot:
            with pytest.raises(TelegramNetworkError) as exc_info:
                await bot.download("id", timeout=DownloadTimeout(sock_read=0.2))
        assert isinstance(exc_info.value.original, asyncio.TimeoutError)
        assert_token_absent(exc_info.value)

    async def test_number_caps_total(self):
        server = FileServer(chunks=20, interval=0.05)
        async with server.bot() as bot:
            with pytest.raises(TelegramNetworkError) as exc_info:
                await bot.download("id", timeout=0.3)
        assert_token_absent(exc_info.value)


class TestStream:
    async def test_chunks(self):
        async with FileServer(chunks=3, interval=0).bot() as bot:
            stream = bot.stream(File(file_id="id", file_unique_id="u"), chunk_size=1)
            assert [chunk async for chunk in stream] == [b"x"] * 3
            assert acquired(bot) == 0

    async def test_break_in_async_with_releases(self):
        async with FileServer(chunks=50, interval=0.01).bot() as bot:
            async with bot.stream("id", chunk_size=1) as stream:
                async for _ in stream:
                    assert acquired(bot) == 1
                    break
            assert acquired(bot) == 0

    async def test_break_releases(self, caplog: pytest.LogCaptureFixture):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            async with FileServer(chunks=50, interval=0.01).bot() as bot:
                async for _ in bot.stream("id", chunk_size=1):
                    assert acquired(bot) == 1
                    break
                await settle()
                assert acquired(bot) == 0
        assert "Task was destroyed" not in caplog.text

    async def test_consumer_error_releases(self):
        async with FileServer(chunks=50, interval=0.01).bot() as bot:
            with pytest.raises(ZeroDivisionError):
                async with bot.stream("id", chunk_size=1) as stream:
                    async for _ in stream:
                        1 / 0  # noqa: B018
            assert acquired(bot) == 0

    async def test_cancel_releases(self):
        async with FileServer(chunks=50, interval=0.05).bot() as bot:
            started = asyncio.Event()

            async def consume() -> None:
                async with bot.stream("id", chunk_size=1) as stream:
                    async for _ in stream:
                        started.set()

            task = asyncio.create_task(consume())
            await started.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert acquired(bot) == 0

    async def test_nothing_requested_before_first_read(self):
        async with FileServer(chunks=1, interval=0).bot() as bot:
            stream = bot.stream("id")
            await stream.aclose()
            assert [chunk async for chunk in stream] == []

    async def test_after_open_failure(self):
        async def fail() -> AsyncGenerator[bytes, None]:
            raise ZeroDivisionError

        stream = DownloadStream(fail)
        with pytest.raises(ZeroDivisionError):
            await anext(stream)
        await stream.aclose()
        with pytest.raises(StopAsyncIteration):
            await anext(stream)

    async def test_retry_after_open_failure(self):
        calls = 0

        async def chunks() -> AsyncGenerator[bytes, None]:
            yield b"ok"

        async def flaky() -> AsyncGenerator[bytes, None]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ZeroDivisionError
            return chunks()

        stream = DownloadStream(flaky)
        with pytest.raises(ZeroDivisionError):
            await anext(stream)
        assert [chunk async for chunk in stream] == [b"ok"]

    async def test_close_during_open(self):
        opened = asyncio.Event()
        release = asyncio.Event()

        async def chunks() -> AsyncGenerator[bytes, None]:
            yield b"late"  # pragma: no cover

        async def slow() -> AsyncGenerator[bytes, None]:
            opened.set()
            await release.wait()
            return chunks()

        stream = DownloadStream(slow)
        task = asyncio.create_task(anext(stream))
        await opened.wait()
        await stream.aclose()
        release.set()
        with pytest.raises(StopAsyncIteration):
            await task
        assert [chunk async for chunk in stream] == []

    def test_wrong_file(self):
        with pytest.raises(TypeError):
            Bot(FAKE_TOKEN).stream(42)  # type: ignore[arg-type]

    async def test_local(self, tmp_path: Path):
        path = tmp_path / "file.bin"
        path.write_bytes(b"local")
        api = TelegramAPIServer.from_base("http://x", is_local=True)
        bot = Bot(FAKE_TOKEN, session=AiohttpSession(api=api))

        async def get_file(file_id: str, **kwargs: Any) -> File:
            return File(file_id=file_id, file_unique_id="u", file_path=str(path))

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(bot, "get_file", get_file)
            async with bot.stream("id") as stream:
                assert [chunk async for chunk in stream] == [b"local"]

    async def test_download_to_path(self, tmp_path: Path):
        destination = tmp_path / "file.bin"
        async with FileServer(chunks=2, interval=0).bot() as bot:
            assert await bot.download("id", destination) is None
        assert destination.read_bytes() == b"xx"

    async def test_download_to_binary_io(self):
        destination = io.BytesIO()
        async with FileServer(chunks=2, interval=0).bot() as bot:
            assert await bot.download("id", destination, seek=False) is destination
        assert destination.getvalue() == b"xx"


class TestLegacySession:
    """A custom session still declaring the 3.x `stream_content(timeout: int = 30)`."""

    @staticmethod
    def session_class() -> type[CustomSession]:
        # A fresh class each time: the check and its warning run once per class
        seen: list[Any] = []

        class LegacySession(CustomSession):
            async def stream_content(
                self, url: str, headers=None, timeout: int = 30, **kwargs: Any
            ):
                seen.append(timeout)
                yield b"legacy"

        LegacySession.seen = seen  # type: ignore[attr-defined]
        return LegacySession

    @pytest.mark.parametrize(
        "timeout,expected",
        [
            (DEFAULT_DOWNLOAD_TIMEOUT, LEGACY_DOWNLOAD_TIMEOUT),
            (5, 5),
            (DownloadTimeout(total=7.5), 7.5),
        ],
    )
    async def test_gets_int(self, timeout: Any, expected: float):
        cls = self.session_class()
        bot = Bot(FAKE_TOKEN, session=cls())
        with pytest.warns(DeprecationWarning, match=r"LegacySession\.stream_content\(\)"):
            result = await bot.download_file(FILE_PATH, timeout=timeout)
        assert result.read() == b"legacy"
        assert cls.seen == [expected]  # type: ignore[attr-defined]

    async def test_warns_once_per_class(self):
        cls = self.session_class()
        bot = Bot(FAKE_TOKEN, session=cls())
        with pytest.warns(DeprecationWarning):
            await bot.download_file(FILE_PATH)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            await bot.download_file(FILE_PATH)
            # URLInputFile reads take the same path
            assert [c async for c in URLInputFile("http://x/y").read(bot)] == [b"legacy"]

    async def test_new_signature_does_not_warn(self):
        received: list[Any] = []

        class NewSession(CustomSession):
            async def stream_content(
                self,
                url: str,
                headers: Any = None,
                timeout: DownloadTimeout | float = DEFAULT_DOWNLOAD_TIMEOUT,
                **kwargs: Any,
            ):
                received.append(timeout)
                yield b""

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            await Bot(FAKE_TOKEN, session=NewSession()).download_file(FILE_PATH, timeout=3)
        assert received == [DownloadTimeout(connect=None, sock_read=None, total=3)]

    def test_forwarding_wrapper_is_not_legacy(self):
        class Wrapper(AiohttpSession):
            def stream_content(self, *args: Any, **kwargs: Any):  # pragma: no cover
                return super().stream_content(*args, **kwargs)

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert _takes_download_timeout(Wrapper)

    @pytest.mark.skipif(sys.version_info < (3, 14), reason="lazy annotations")
    def test_unresolvable_annotation(self):
        class LazySession(CustomSession):
            async def stream_content(
                self,
                url: str,
                headers: Unresolvable = None,  # noqa: F821
                timeout: DownloadTimeout | float = DEFAULT_DOWNLOAD_TIMEOUT,
                **kwargs: Any,
            ):
                yield b""  # pragma: no cover

        assert _takes_download_timeout(LazySession)
