"""
Record a real bot's Bot API traffic as a raw trace (dev tool, never shipped).

Usage::

    CORPUS_BOT_TOKEN=... uv run python -m benchmarks.record.recorder --limit 200

The bot long-polls with every update type allowed, answers each message (with an inline keyboard,
so its buttons produce callback queries), each callback query and each inline query, and stops
after ``--limit`` updates. Every request is written to ``benchmarks/record/raw/`` (gitignored) as
one JSON line: method, wire-form params, HTTP status and the raw response, captured before
aiogram decodes it, so a response that fails to decode is recorded too.

The raw file contains the token-free but **unredacted** traffic: run
``python -m benchmarks.record.redact`` on it and review the result before committing anything.
"""

import argparse
import asyncio
import datetime
import json
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TextIO

from aiogram import Bot, Dispatcher, __api_version__, __version__
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.methods import TelegramMethod
from aiogram.methods.base import Response, TelegramType
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InputFile,
    Message,
    TelegramObject,
    Update,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

RAW_DIR = Path(__file__).parent / "raw"


class RecordingSession(AiohttpSession):
    """
    Writes each request/response pair from ``check_response``.

    Not a request middleware: a middleware only sees the decoded response, and loses the raw body
    exactly when decoding fails (the forward-compatibility cases worth recording).
    """

    def __init__(self, sink: TextIO, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.sink = sink

    def check_response(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        status_code: int,
        content: str,
    ) -> Response[TelegramType]:
        files: dict[str, InputFile] = {}
        params = {
            key: prepared
            for key, value in method.model_dump(warnings=False).items()
            if (prepared := self.prepare_value(value, bot=bot, files=files, _dumps_json=False))
            is not None
        }
        record: dict[str, Any] = {
            "method": method.__api_method__,
            "params": params,
            "files": {key: file.filename for key, file in files.items()},
            "status": status_code,
        }
        try:
            record["response"] = json.loads(content)
        except ValueError:
            record["raw"] = content
        self.sink.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.sink.flush()
        return super().check_response(bot, method, status_code, content)


async def record(token: str, output: Path, limit: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as sink:
        provenance = {
            "source": "recorded",
            "date": datetime.date.today().isoformat(),  # noqa: DTZ011
            "aiogram": __version__,
            "bot_api": __api_version__,
            "redacted": False,
        }
        sink.write(json.dumps({"provenance": provenance}) + "\n")

        bot = Bot(token, session=RecordingSession(sink))
        dp = Dispatcher()
        seen = 0

        async def count(
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
        ) -> Any:
            nonlocal seen
            seen += 1
            try:
                return await handler(event, data)
            finally:
                if seen == limit:
                    await dp.stop_polling()

        dp.update.outer_middleware(count)

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="tap", callback_data="corpus:tap")
        keyboard.button(text="inline", switch_inline_query_current_chat="corpus")
        markup = keyboard.as_markup()

        @dp.message()
        async def on_message(message: Message) -> None:
            await message.answer(f"recorded {seen}/{limit}", reply_markup=markup)

        @dp.callback_query()
        async def on_callback(query: CallbackQuery) -> None:
            await query.answer(f"recorded {seen}/{limit}")

        @dp.inline_query()
        async def on_inline(query: InlineQuery) -> None:
            await query.answer([], cache_time=0)

        allowed = [name for name in Update.model_fields if name != "update_id"]
        await dp.start_polling(bot, allowed_updates=allowed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--limit", type=int, default=200, help="stop after this many updates")
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()
    token = os.environ.get("CORPUS_BOT_TOKEN")
    if not token:
        parser.error("set CORPUS_BOT_TOKEN to the test bot's token")
    output = args.output or RAW_DIR / f"trace-{datetime.datetime.now():%Y%m%d-%H%M%S}.jsonl"  # noqa: DTZ005
    asyncio.run(record(token, output, args.limit))


if __name__ == "__main__":
    main()
