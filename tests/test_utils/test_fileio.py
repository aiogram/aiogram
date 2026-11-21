import asyncio
import hashlib
import os
import threading
from contextlib import aclosing
from pathlib import Path

import pytest

from aiogram.utils import _fileio
from aiogram.utils._fileio import iter_file, write_stream


async def stream_of(*chunks: bytes):
    for chunk in chunks:
        yield chunk


class CountingOpen:
    """Wraps ``open`` and counts handles that are open right now."""

    def __init__(self, monkeypatch, gate: threading.Event | None = None):
        self.opened = []
        self.gate = gate
        self.real = open
        monkeypatch.setattr("builtins.open", self)

    def __call__(self, *args, **kwargs):
        if self.gate is not None:
            self.gate.wait(5)
        f = self.real(*args, **kwargs)
        self.opened.append(f)
        return f

    @property
    def leaked(self) -> int:
        return sum(not f.closed for f in self.opened)


class TestFileIO:
    async def test_roundtrip_5mb(self, tmp_path: Path):
        data = os.urandom(5 * 1024 * 1024)
        src, dst = tmp_path / "src", tmp_path / "dst"
        src.write_bytes(data)

        await write_stream(dst, iter_file(src, 64 * 1024))

        assert hashlib.sha256(dst.read_bytes()).hexdigest() == hashlib.sha256(data).hexdigest()

    async def test_chunks(self, tmp_path: Path):
        src = tmp_path / "src"
        src.write_bytes(b"abcde")
        assert [c async for c in iter_file(src, 2)] == [b"ab", b"cd", b"e"]

    async def test_closed_on_end(self, tmp_path: Path, monkeypatch):
        counter = CountingOpen(monkeypatch)
        src = tmp_path / "src"
        src.write_bytes(b"abc")
        assert [c async for c in iter_file(src, 1)] == [b"a", b"b", b"c"]
        assert len(counter.opened) == 1
        assert counter.leaked == 0

    async def test_closed_on_early_aclose(self, tmp_path: Path, monkeypatch):
        counter = CountingOpen(monkeypatch)
        src = tmp_path / "src"
        src.write_bytes(b"abc")
        async with aclosing(iter_file(src, 1)) as chunks:
            assert await anext(chunks) == b"a"
            assert counter.leaked == 1
        assert counter.leaked == 0

    async def test_closed_on_cancel_mid_read(self, tmp_path: Path, monkeypatch):
        counter = CountingOpen(monkeypatch)
        src = tmp_path / "src"
        src.write_bytes(b"x" * 1024)
        started = asyncio.Event()

        async def consume():
            async for _ in iter_file(src, 1):
                started.set()
                await asyncio.sleep(10)

        task = asyncio.ensure_future(consume())
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0.05)
        assert counter.leaked == 0

    @pytest.mark.parametrize("mode_writer", [False, True])
    async def test_cancel_while_open_in_flight(self, tmp_path: Path, monkeypatch, mode_writer):
        gate = threading.Event()
        counter = CountingOpen(monkeypatch, gate)
        src = tmp_path / "src"
        src.write_bytes(b"abc")

        async def run():
            if mode_writer:
                await write_stream(tmp_path / "dst", stream_of(b"a"))
            else:
                async for _ in iter_file(src, 1):
                    pass

        task = asyncio.ensure_future(run())
        await asyncio.sleep(0.05)  # the worker thread is blocked inside open()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        gate.set()
        for _ in range(100):
            if counter.opened:
                break
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.05)
        assert len(counter.opened) == 1
        assert counter.leaked == 0

    async def test_open_error_propagates(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            await anext(iter_file(tmp_path / "missing", 1))

    async def test_closed_when_stream_fails(self, tmp_path: Path, monkeypatch):
        counter = CountingOpen(monkeypatch)

        async def bad():
            yield b"a"
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            await write_stream(tmp_path / "dst", bad())
        assert counter.leaked == 0

    def test_close_callback_skips_failed_open(self):
        loop = asyncio.new_event_loop()
        try:
            failed = loop.create_future()
            failed.set_exception(OSError())
            failed.exception()
            _fileio._close_opened(failed)
            cancelled = loop.create_future()
            cancelled.cancel()
            _fileio._close_opened(cancelled)
        finally:
            loop.close()
