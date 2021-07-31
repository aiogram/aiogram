from typing import Optional, TypeVar

from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType

ErrorType = TypeVar("ErrorType")


class TelegramAPIError(Exception):
    url: Optional[str] = None

    def __init__(
        self,
        method: TelegramMethod[TelegramType],
        message: str,
    ) -> None:
        self.method = method
        self.message = message

    def render_description(self) -> str:
        return self.message

    def __str__(self) -> str:
        message = [self.render_description()]
        if self.url:
            message.append(f"(background on this error at: {self.url})")
        return "\n".join(message)
