from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, NoReturn

from aiogram.methods import Response, TelegramMethod

if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.client.session.base import BaseSession


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


def raise_api_error(
    session: BaseSession,
    bot: Bot,
    method: TelegramMethod[Any],
    description: str,
    error_code: int = HTTPStatus.BAD_REQUEST,
) -> NoReturn:
    """
    Fail a call the way the real API would.

    Routed through :meth:`aiogram.client.session.base.BaseSession.check_response` on
    purpose, so the exception type, its message and the error pipeline under test are
    the production ones rather than a lookalike.
    """
    response: Response[Any] = Response[method.__returning__](  # type: ignore
        ok=False,
        error_code=error_code,
        description=description,
    )
    session.check_response(
        bot=bot,
        method=method,
        status_code=error_code,
        content=response.model_dump_json(),
    )
    msg = "check_response did not raise for a failed response"  # pragma: no cover
    raise RuntimeError(msg)  # pragma: no cover
