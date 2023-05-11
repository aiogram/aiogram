from typing import Any

import msgspec.json

from aiogram import Bot, Dispatcher

from ..types import UNSET_PARSE_MODE
from ..types.base import UNSET_DISABLE_WEB_PAGE_PREVIEW, UNSET_PROTECT_CONTENT


class ASGIApplication:
    def __init__(
        self,
        bot: Bot,
        dispatcher: Dispatcher,
        handle_in_background: bool = False,
        lifespan_data: dict = None,
        **data: Any,
    ) -> None:
        """
        :param dispatcher: instance of :class:`aiogram.dispatcher.dispatcher.Dispatcher`
        :param handle_in_background: immediately respond to the Telegram instead of
            waiting end of handler process
        """
        self.bot = bot
        self.dispatcher = dispatcher
        self.handle_in_background = handle_in_background
        self.data = data
        lifespan_data = lifespan_data or {}
        self.lifespan_data = {
            "bot": self.bot,
            "dispatcher": self.dispatcher,
            **lifespan_data,
            **self.dispatcher.workflow_data,
        }

    async def _read_body(self, receive):
        """
        Read and return the entire body from an incoming ASGI message.
        """
        body = b""
        more_body = True

        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        return body

    async def _lifespan(self, scope, receive, send):
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await self.dispatcher.emit_startup(**self.lifespan_data)
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await self.dispatcher.emit_shutdown(**self.lifespan_data)
                await send({"type": "lifespan.shutdown.complete"})
                return

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            await self._lifespan(scope, receive, send)
            return

        result = await self.dispatcher.feed_webhook_update(
            self.bot,
            await self._read_body(receive),
            **self.data,
        )

        if result is not None:
            result.method = result.__api_method__

        def enc_hook(obj):
            if obj is UNSET_PARSE_MODE:
                return self.bot.parse_mode
            if obj is UNSET_DISABLE_WEB_PAGE_PREVIEW:
                return self.bot.disable_web_page_preview
            if obj is UNSET_PROTECT_CONTENT:
                return self.bot.protect_content
            raise ValueError(f"Unknown object: {obj}")

        response = msgspec.json.encode(result, enc_hook=enc_hook)

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(response)).encode()),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": response,
            }
        )
