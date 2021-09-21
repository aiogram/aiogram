from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from ..types import PassportElementError
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class SetPassportDataErrors(TelegramMethod[bool]):
    """
    Informs a user that some of the Telegram Passport elements they provided contains errors. The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns :code:`True` on success.
    Use this if the data submitted by the user doesn't satisfy the standards your service requires for any reason. For example, if a birthday date seems invalid, a submitted document is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message to make sure the user knows how to correct the issues.

    Source: https://core.telegram.org/bots/api#setpassportdataerrors
    """

    __returning__ = bool

    user_id: int
    """User identifier"""
    errors: List[PassportElementError]
    """A JSON-serialized array describing the errors"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="setPassportDataErrors", data=data)
