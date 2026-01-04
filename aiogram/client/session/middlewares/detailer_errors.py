import sys
import time

from aiogram import Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import Response, TelegramMethod
from aiogram.methods.base import TelegramType

_UNSUPPORTED_PYTHON_VERSION_ERROR_MESSAGE = """
ContextInErrorsMiddleware requires Python 3.11+ in order it uses `Exception.add_note method`.
Read more: https://docs.python.org/3/library/exceptions.html#BaseException.add_note
"""


class ContextInErrorsMiddleware(BaseRequestMiddleware):
    def __init__(
        self,
        show_method: bool = True,
        show_url: bool = True,
        show_duration: bool = True,
        show_arguments: bool = True,
    ) -> None:
        if sys.version_info < (3, 11):
            raise RuntimeError(_UNSUPPORTED_PYTHON_VERSION_ERROR_MESSAGE)

        self.show_method = show_method
        self.show_url = show_url
        self.show_duration = show_duration

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        start = time.perf_counter()
        try:
            return await make_request(bot, method)
        except TelegramAPIError as e:
            if sys.version_info >= (3, 11):
                url = bot.session.api.api_url(
                    token=f"{bot.id}:TOKEN", method=method.__api_method__
                )

                if self.show_method:
                    e.add_note(f"method: {type(method).__name__}({method})")
                if self.show_url:
                    e.add_note(f"url: {url}")
                if self.show_duration:
                    e.add_note(f"duration: {time.perf_counter() - start:.3f}s")
            raise e
