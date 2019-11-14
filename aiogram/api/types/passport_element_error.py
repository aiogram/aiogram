from __future__ import annotations

from .base import TelegramObject


class PassportElementError(TelegramObject):
    """
    This object represents an error in the Telegram Passport element which was submitted that
    should be resolved by the user. It should be one of:
     - PassportElementErrorDataField
     - PassportElementErrorFrontSide
     - PassportElementErrorReverseSide
     - PassportElementErrorSelfie
     - PassportElementErrorFile
     - PassportElementErrorFiles
     - PassportElementErrorTranslationFile
     - PassportElementErrorTranslationFiles
     - PassportElementErrorUnspecified

    Source: https://core.telegram.org/bots/api#passportelementerror
    """
