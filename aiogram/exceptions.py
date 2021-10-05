from textwrap import indent
from typing import List, Optional, Set

from pydantic import ValidationError

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


class FiltersResolveError(DetailedAiogramError):
    def __init__(self, unresolved_fields: Set[str], possible_cases: List[ValidationError]) -> None:
        possible_cases_str = "\n".join(
            "  - " + indent(str(e), " " * 4).lstrip() for e in possible_cases
        )
        message = f"Unknown keyword filters: {unresolved_fields}"
        if possible_cases_str:
            message += f"\n  Possible cases:\n{possible_cases_str}"

        super().__init__(message=message)
        self.unresolved_fields = unresolved_fields
        self.possible_cases = possible_cases
