from typing import Any, Optional

from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType


class AiogramError(Exception):
    pass


class DetailedAiogramError(AiogramError):
    url: Optional[str] = None

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        message = self.message
        if self.url:
            message += f"\n(background on this error at: {self.url})"
        return message

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"


class TelegramAPIError(DetailedAiogramError):
    def __init__(
        self,
        method: TelegramMethod[TelegramType],
        message: str,
    ) -> None:
        super().__init__(message=message)
        self.method = method


class TelegramNetworkError(TelegramAPIError):
    pass


class TelegramRetryAfter(TelegramAPIError):
    url = "https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this"

    def __init__(
        self,
        method: TelegramMethod[TelegramType],
        message: str,
        retry_after: int,
    ) -> None:
        description = f"Flood control exceeded on method {type(method).__name__!r}"
        if chat_id := getattr(method, "chat_id", None):
            description += f" in chat {chat_id}"
        description += f". Retry in {retry_after} seconds."
        description += f"\nOriginal description: {message}"

        super().__init__(method=method, message=description)
        self.retry_after = retry_after


class TelegramMigrateToChat(TelegramAPIError):
    url = "https://core.telegram.org/bots/api#responseparameters"

    def __init__(
        self,
        method: TelegramMethod[TelegramType],
        message: str,
        migrate_to_chat_id: int,
    ) -> None:
        description = f"The group has been migrated to a supergroup with id {migrate_to_chat_id}"
        if chat_id := getattr(method, "chat_id", None):
            description += f" from {chat_id}"
        description += f"\nOriginal description: {message}"
        super().__init__(method=method, message=message)
        self.migrate_to_chat_id = migrate_to_chat_id


class TelegramBadRequest(TelegramAPIError):
    pass


class TelegramNotFound(TelegramAPIError):
    pass


class TelegramConflictError(TelegramAPIError):
    pass


class TelegramUnauthorizedError(TelegramAPIError):
    pass


class TelegramForbiddenError(TelegramAPIError):
    pass


class TelegramServerError(TelegramAPIError):
    pass


class RestartingTelegram(TelegramServerError):
    pass


class TelegramEntityTooLarge(TelegramNetworkError):
    url = "https://core.telegram.org/bots/api#sending-files"


class ClientDecodeError(AiogramError):
    def __init__(self, message: str, original: Exception, data: Any) -> None:
        self.message = message
        self.original = original
        self.data = data

    def __str__(self) -> str:
        original_type = type(self.original)
        return (
            f"{self.message}\n"
            f"Caused from error: {original_type.__module__}.{original_type.__name__}: {self.original}\n"
            f"Content: {self.data}"
        )
