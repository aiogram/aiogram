from typing import ClassVar, List, Match, Optional, TypeVar

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


class DetailedTelegramAPIError(TelegramAPIError):
    patterns: ClassVar[List[str]]

    def __init__(
        self,
        method: TelegramMethod[TelegramType],
        message: str,
        match: Match[str],
    ) -> None:
        super().__init__(method=method, message=message)
        self.match: Match[str] = match
