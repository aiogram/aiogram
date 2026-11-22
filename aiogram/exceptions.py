from typing import Any

from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType


class AiogramError(Exception):
    """
    Base exception for all aiogram errors.
    """


class DetailedAiogramError(AiogramError):
    """
    Base exception for all aiogram errors with detailed message.
    """

    url: str | None = None

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        message = self.message
        if self.url:
            message += f"\n(background on this error at: {self.url})"
        return message

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"


class CallbackAnswerException(AiogramError):
    """
    Exception for callback answer.
    """


class SceneException(AiogramError):
    """
    Exception for scenes.
    """


class TelegramAPIError(DetailedAiogramError):
    """
    Base exception for all Telegram API errors.
    """

    label: str = "Telegram server says"

    def __init__(
        self,
        method: TelegramMethod[TelegramType],
        message: str,
    ) -> None:
        super().__init__(message=message)
        self.method = method

    def __str__(self) -> str:
        original_message = super().__str__()
        return f"{self.label} - {original_message}"


class TelegramNetworkError(TelegramAPIError):
    """
    Base exception for all Telegram network errors.

    Its message never contains the bot token: it names the HTTP client error type and the
    request URL with the token replaced by ``<bot id>:***``. The HTTP client error itself
    is kept on :attr:`original` instead of being chained (``__cause__`` is ``None``),
    because its text may contain the token.
    """

    label = "HTTP Client says"
    method: TelegramMethod[Any] | None  # type: ignore[assignment]
    """The API method, or ``None`` when a file download failed."""
    original: BaseException | None
    """The HTTP client error, or ``None`` when the error is not a transport failure."""
    request_sent: bool | None
    """
    ``False`` when the request is known not to have reached the server (connection, proxy
    tunnel or invalid URL errors before any redirect), ``True`` when a response arrived
    (an HTTP error status, a redirect, a 413), ``None`` when it is unknown (a timeout or
    a connection lost mid-request). A retry of a non-idempotent method is
    only safe when this is ``False``.
    """

    def __init__(
        self,
        method: TelegramMethod[Any] | None,
        message: str,
        original: BaseException | None = None,
        request_sent: bool | None = None,
    ) -> None:
        super().__init__(method=method, message=message)  # type: ignore[arg-type]
        self.original = original
        self.request_sent = request_sent


class TelegramRetryAfter(TelegramAPIError):
    """
    Exception raised when flood control exceeds.
    """

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
    """
    Exception raised when chat has been migrated to a supergroup.
    """

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
        super().__init__(method=method, message=description)
        self.migrate_to_chat_id = migrate_to_chat_id


class TelegramBadRequest(TelegramAPIError):
    """
    Exception raised when request is malformed.
    """


class TelegramNotFound(TelegramAPIError):
    """
    Exception raised when chat, message, user, etc. not found.
    """


class TelegramConflictError(TelegramAPIError):
    """
    Exception raised when bot token is already used by another application in polling mode.
    """


class TelegramUnauthorizedError(TelegramAPIError):
    """
    Exception raised when bot token is invalid.
    """


class TelegramForbiddenError(TelegramAPIError):
    """
    Exception raised when bot is kicked from chat or etc.
    """


class TelegramServerError(TelegramAPIError):
    """
    Exception raised when Telegram server returns 5xx error.
    """


class RestartingTelegram(TelegramServerError):
    """
    Exception raised when Telegram server is restarting.

    It seems like this error is not used by Telegram anymore,
    but it's still here for backward compatibility.

    Currently, you should expect that Telegram can raise RetryAfter (with timeout 5 seconds)
     error instead of this one.
    """


class TelegramEntityTooLarge(TelegramNetworkError):
    """
    Exception raised when you are trying to send a file that is too large.
    """

    url = "https://core.telegram.org/bots/api#sending-files"


class ClientDecodeError(AiogramError):
    """
    Exception raised when client can't decode response. (Malformed response, etc.)
    """

    def __init__(self, message: str, original: Exception, data: Any) -> None:
        self.message = message
        self.original = original
        self.data = data

    def __str__(self) -> str:
        original_type = type(self.original)
        return (
            f"{self.message}\n"
            f"Caused from error: "
            f"{original_type.__module__}.{original_type.__name__}: {self.original}\n"
            f"Content: {self.data}"
        )


class DataNotDictLikeError(DetailedAiogramError):
    """
    Exception raised when data is not dict-like.
    """
