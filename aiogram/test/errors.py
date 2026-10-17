from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, NoReturn

from aiogram.methods import Response, TelegramMethod
from aiogram.types import ResponseParameters

if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.client.session.base import BaseSession

    from .rejections import Rejection


class ApiRejection(Exception):
    """
    Raised when the modeled world refuses a call the way the Bot API would refuse it.

    The counterpart of :class:`aiogram.test.WorldLookupError`, and the whole reason the two
    are different types. Both used to be one, and
    :meth:`aiogram.test.BotTestEnvironment.handle_call` turned it into a
    :class:`~aiogram.exceptions.TelegramBadRequest` — which is right for *this* half and
    quietly wrong for the other. A rejection here is something Telegram itself would answer:
    forwarding a message that does not exist, demoting the chat owner, closing a closed
    poll. Bot code legitimately catches those, and a test of that ``except`` branch is a
    real test. A blueprint gap is not: "User 999999 is not declared in the blueprint" is a
    broken test setup, and converting it made the bot's own error handling swallow it and
    exercise the wrong branch in silence. So that half raises
    :class:`~aiogram.test.WorldLookupError`, which nothing converts and nothing catches, and
    the test fails with the message that says how to fix it.

    The description is Telegram's wording, without the ``Bad Request:``
    prefix that ``handle_call`` adds, and best-effort: the error code
    and the exception type it becomes are the contract. The ones that
    are guaranteed too are listed in :mod:`aiogram.test.rejections`.

    ``error_code`` is the HTTP status the rejection comes back with:
    400 by default, 403 for a bot that is not in the chat, 429 for a
    flood. ``handle_call`` names it by the prefix the Bot API gives
    it, and the session turns it into the exception type ``aiogram``
    maps that code to. A 429 carries ``retry_after``, which is what
    makes it a :class:`~aiogram.exceptions.TelegramRetryAfter`, and
    no other code does, so a mismatch is a :class:`ValueError`.
    """

    def __init__(
        self,
        description: str,
        *,
        error_code: int = HTTPStatus.BAD_REQUEST,
        retry_after: int | None = None,
        rejection: Rejection | None = None,
    ) -> None:
        if (retry_after is None) == (error_code == HTTPStatus.TOO_MANY_REQUESTS):
            msg = "a 429 carries retry_after, and nothing else does"
            raise ValueError(msg)
        super().__init__(description)
        self.description = description
        self.error_code = error_code
        self.retry_after = retry_after
        #: The declaration the text came from, if it has one.
        self.rejection = rejection

    @property
    def prefixed(self) -> str:
        """The description as the Bot API server sends it."""
        prefix = _ERROR_PREFIXES.get(self.error_code)
        if prefix is None:
            try:
                prefix = HTTPStatus(self.error_code).phrase
            except ValueError:
                prefix = "Error"
        return f"{prefix}: {self.description}"


#: The prefix the Bot API server puts before a refusal's text.
_ERROR_PREFIXES: dict[int, str] = {
    HTTPStatus.BAD_REQUEST: "Bad Request",
    HTTPStatus.UNAUTHORIZED: "Unauthorized",
    HTTPStatus.FORBIDDEN: "Forbidden",
    HTTPStatus.NOT_FOUND: "Not Found",
    HTTPStatus.CONFLICT: "Conflict",
    HTTPStatus.REQUEST_ENTITY_TOO_LARGE: "Request Entity Too Large",
    HTTPStatus.TOO_MANY_REQUESTS: "Too Many Requests",
    HTTPStatus.INTERNAL_SERVER_ERROR: "Internal Server Error",
}


class NoFileContentError(LookupError):
    """
    Raised when a download asks for content the environment does not hold.

    The fake never reads the filesystem or the network, so content has to come from a
    declaration or from an upload that carried its own bytes.
    """

    def __init__(self, file_id: str) -> None:
        super().__init__(
            f"No content is registered for file_id={file_id!r}. Declare it with "
            f"`blueprint.add_file({file_id!r}, b'...')`, send it as a `BufferedInputFile` "
            f"so the upload registers its bytes, or override the call with "
            f"`env.on(GetFile).returns(...)`. Note that `FSInputFile` and `URLInputFile` "
            f"are never read: a test environment does not touch the disk or the network."
        )
        self.file_id = file_id


class WaitTimeoutError(TimeoutError):
    """
    Raised when a waiting helper gives up before its condition became true.

    Subclasses the built-in :class:`TimeoutError`, so a test that catches the generic
    timeout — ``pytest.raises(TimeoutError)`` — catches this too. The message is assembled
    by the caller, which knows what was being waited for and what the world holds instead.
    """


class BackgroundTaskError(AssertionError):
    """
    Raised when one of the bot's own background tasks failed.

    :meth:`~aiogram.test.BotTestEnvironment.wait_for_background_tasks`
    raises it for a task that ended with an exception nobody retrieved,
    and :class:`DrainedTaskError` is the same failure as ``drain()``
    finds it, so ``pytest.raises(BackgroundTaskError)`` catches both.
    The first failure is chained as ``__cause__``.
    """


class DrainedTaskError(BackgroundTaskError):
    """
    Raised when a task :meth:`aiogram.test.BotTestEnvironment.drain` cancelled had already
    failed of its own accord.

    ``drain()`` exists to silence the ``Task was destroyed but it is pending!`` noise a
    fire-and-forget background task leaves behind, and silencing that noise means
    *retrieving* each task's result. Retrieving and then discarding it would make the
    cleanup helper the thing that hides a real bug: a night timer that died with a
    ``KeyError`` would look exactly like one that was cancelled on time. So the failures
    come back out here instead, with the first one chained as ``__cause__`` so its real
    traceback is one line away.

    An :class:`AssertionError` because that is what it is — the bot under test did
    something wrong, and pytest renders it as a test failure rather than as an error in the
    toolkit.
    """


def raise_api_error(
    session: BaseSession,
    bot: Bot,
    method: TelegramMethod[Any],
    description: str,
    error_code: int = HTTPStatus.BAD_REQUEST,
    retry_after: int | None = None,
) -> NoReturn:
    """
    Fail a call the way the real API would.

    Routed through :meth:`aiogram.client.session.base.BaseSession.check_response` on
    purpose, so the exception type, its message and the error pipeline under test are
    the production ones rather than a lookalike. ``retry_after`` goes
    into the response's ``parameters``, as a flood refusal carries it.
    """
    if (retry_after is None) == (error_code == HTTPStatus.TOO_MANY_REQUESTS):
        msg = "a 429 carries retry_after, and nothing else does"
        raise ValueError(msg)
    response: Response[Any] = Response[method.__returning__](  # type: ignore
        ok=False,
        error_code=error_code,
        description=description,
        parameters=None if retry_after is None else ResponseParameters(retry_after=retry_after),
    )
    session.check_response(
        bot=bot,
        method=method,
        status_code=error_code,
        content=response.model_dump_json(),
    )
    msg = "check_response did not raise for a failed response"  # pragma: no cover
    raise RuntimeError(msg)  # pragma: no cover
