from __future__ import annotations

import io
import uuid
import asyncio
from urllib.parse import urlencode, urlparse, ParseResult
from collections import deque
from typing import AsyncGenerator, Callable, Optional, TypeVar, Set, Deque, Tuple, Dict, cast
from contextlib import asynccontextmanager

from aiogram.api.methods import Request, TelegramMethod

from aiogram.api.client.session.base import PRODUCTION, BaseSession, TelegramAPIServer


T = TypeVar("T")
StreamType = Tuple[asyncio.StreamReader, asyncio.StreamWriter]


def _get_boundary() -> bytes:
    return b"%032x" % uuid.uuid4().int


async def _get_headers(reader: asyncio.StreamReader) -> Optional[bytes]:
    headers = await reader.readuntil(b"\r\n\r\n")
    if headers[-4:] != b"\r\n\r\n":
        return None
    return headers


class AsyncioSession(BaseSession):
    def __init__(
        self,
        api: TelegramAPIServer = PRODUCTION,
        json_loads: Optional[Callable] = None,
        json_dumps: Optional[Callable] = None,
    ) -> None:
        super().__init__(
            api=api, json_loads=json_loads, json_dumps=json_dumps,
        )

        self._closed = False
        # we use stream req-time semaphore
        self._semaphore = asyncio.Semaphore()

        # keep some connections' underlying socket open with the help of the following dss
        self._connections_deque: Deque[Optional[StreamType]] = deque()
        self._busy_connections: Set[Optional[StreamType]] = set()

    async def _encode_multipart_formdata(self, request: Request) -> Tuple[bytes, bytes]:
        boundary = _get_boundary()
        body = io.BytesIO()

        for key, val in request.data.items():
            if val is None:
                continue

            part = (
                b"--%b\r\n"
                b'content-disposition: form-data; name="%b"\r\n\r\n'
                b"%b"
                b"\r\n" % (boundary, key.encode(), str(self.prepare_value(val)).encode())
            )

            body.write(part)

        for key, file in request.files.items():  # type: ignore
            headers = (
                b"--%b\r\n"
                b"content-disposition:"
                b" form-data;"
                b' name="%b";'
                b' filename="%b"'
                b"\r\n\r\n" % (boundary, key.encode(), (file.filename or key).encode(),)
            )

            body.write(headers)

            async for chunk in file.read(file.chunk_size):
                body.write(chunk)

            body.write(b"\r\n")

        body.write(b"--%b--\r\n\r\n" % boundary)
        return b"multipart/form-data; boundary=%b" % boundary, body.getvalue()

    def _encode_formdata(self, request: Request) -> Tuple[bytes, bytes]:
        raw_data: Dict[str, str] = {}
        for key, val in request.data.items():
            if val is None:
                continue
            raw_data[key] = str(self.prepare_value(val))
        data = urlencode(raw_data)
        return b"application/x-www-form-urlencoded", data.encode()

    async def form_request(self, parsed: ParseResult, request: Request):
        plain_http = b"POST %b HTTP/1.1\r\n" b"host: %b\r\n" % (
            str(parsed.path).encode(),
            str(parsed.hostname).encode(),
        )

        if request.files:
            content_type, data = await self._encode_multipart_formdata(request)
        else:
            content_type, data = self._encode_formdata(request)

        plain_http += (
            b"content-length: %i\r\n"
            b"content-type: %b\r\n"
            b"\r\n"
            b"%b" % (len(data or ""), content_type, data)
        )

        return plain_http

    @asynccontextmanager
    async def _get_stream(self, host: str, port: int) -> AsyncGenerator[StreamType, None]:  # type: ignore
        await self._semaphore.acquire()
        rw = self._connections_deque.popleft() if self._connections_deque else None
        self._busy_connections.add(rw)
        try:
            if rw is None:
                rw = await asyncio.open_connection(host=host, port=port, ssl=True)
            yield rw
        finally:
            self._busy_connections.discard(rw)
            self._connections_deque.append(rw)
            self._semaphore.release()

    async def make_request(self, token: str, method: TelegramMethod[T]) -> T:
        request = method.build_request()
        parsed = urlparse(self.api.api_url(token=token, method=request.method))
        plain_http = await self.form_request(parsed, request)

        async with self._get_stream(
            parsed.hostname, parsed.port or 443
        ) as stream:  # type: StreamType
            r, w = stream
            w.write(plain_http)
            await w.drain()

            headers = await _get_headers(r)
            if not headers:
                raise asyncio.CancelledError("Could not properly read headers")

            headers = headers.lower()

            index = headers.index(b"content-length:") + 16
            json_data = self.json_loads(
                await r.readexactly(int(headers[index : headers.index(b"\r", index)]))
            )

        response = method.build_response(json_data)
        self.raise_for_status(response)
        return cast(T, response.result)

    async def stream_content(
        self, url: str, timeout: int, chunk_size: int
    ) -> AsyncGenerator[bytes, None]:
        yield b""  # todo

    async def close(self):
        if self._closed:
            return

        self._closed = True

        async def _close(_: asyncio.StreamReader, w: asyncio.StreamWriter):
            w.close()
            await w.wait_closed()

        await asyncio.gather(
            *(_close(*rw) for rw in (*self._connections_deque, *self._busy_connections) if rw)
        )

        self._connections_deque = deque([None] * len(self._connections_deque))
        self._busy_connections.clear()
