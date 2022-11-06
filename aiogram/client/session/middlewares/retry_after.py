import asyncio
import time

from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
from aiogram.methods import GetUpdates, TelegramMethod
from aiogram.methods.base import Response, TelegramType


class RetryAfterMiddleware(BaseRequestMiddleware):
    def __init__(self, max_retry_timeout: float = 10):
        self.max_retry_timeout = max_retry_timeout

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: "Bot",
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        if isinstance(method, GetUpdates):
            # Get updates retried in polling process
            return await make_request(bot, method)

        start = time.monotonic()

        while True:
            try:
                result = await make_request(bot, method)
            except TelegramRetryAfter as e:
                error = e
                sleep_interval = e.retry_after
            except TelegramNetworkError as e:
                error = e
                sleep_interval = 1
            else:
                break

            request_time = time.monotonic() + sleep_interval
            if request_time - start < 0:
                raise error

            await asyncio.sleep(sleep_interval)

        return result
