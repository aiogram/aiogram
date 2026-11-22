"""Chunked file IO on ``asyncio.to_thread``."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import IO


async def _open(path: str | Path, mode: str) -> IO[bytes]:
    # The open runs in a worker thread and cannot be interrupted: when the caller is cancelled
    # meanwhile, the handle is closed by the callback once the open finishes, so it never leaks.
    task = asyncio.ensure_future(asyncio.to_thread(open, path, mode))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        task.add_done_callback(_close_opened)
        raise


def _close_opened(task: asyncio.Future[IO[bytes]]) -> None:
    if not task.cancelled() and task.exception() is None:
        task.result().close()


async def iter_file(path: str | Path, chunk_size: int) -> AsyncGenerator[bytes, None]:
    f = await _open(path, "rb")
    try:
        while chunk := await asyncio.to_thread(f.read, chunk_size):
            yield chunk
    finally:
        # shielded: the handle is closed even if the surrounding task is being cancelled
        await asyncio.shield(asyncio.to_thread(f.close))


async def write_stream(path: str | Path, stream: AsyncGenerator[bytes, None]) -> None:
    f = await _open(path, "wb")
    try:
        async for chunk in stream:
            await asyncio.to_thread(f.write, chunk)
    finally:
        await asyncio.shield(asyncio.to_thread(f.close))
