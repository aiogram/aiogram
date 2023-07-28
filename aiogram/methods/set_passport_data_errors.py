from __future__ import annotations

from typing import List, Union

from ..types import (
    PassportElementErrorDataField,
    PassportElementErrorFile,
    PassportElementErrorFiles,
    PassportElementErrorFrontSide,
    PassportElementErrorReverseSide,
    PassportElementErrorSelfie,
    PassportElementErrorTranslationFile,
    PassportElementErrorTranslationFiles,
    PassportElementErrorUnspecified,
)
from .base import TelegramMethod


class SetPassportDataErrors(TelegramMethod[bool]):
    """
    Informs a user that some of the Telegram Passport elements they provided contains errors. The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns :code:`True` on success.
    Use this if the data submitted by the user doesn't satisfy the standards your service requires for any reason. For example, if a birthday date seems invalid, a submitted document is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message to make sure the user knows how to correct the issues.

    Source: https://core.telegram.org/bots/api#setpassportdataerrors
    """

    __returning__ = bool
    __api_method__ = "setPassportDataErrors"

    user_id: int
    """User identifier"""
    errors: List[
        Union[
            PassportElementErrorDataField,
            PassportElementErrorFrontSide,
            PassportElementErrorReverseSide,
            PassportElementErrorSelfie,
            PassportElementErrorFile,
            PassportElementErrorFiles,
            PassportElementErrorTranslationFile,
            PassportElementErrorTranslationFiles,
            PassportElementErrorUnspecified,
        ]
    ]
    """A JSON-serialized array describing the errors"""
