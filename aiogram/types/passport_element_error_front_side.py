from __future__ import annotations

from pydantic import Field

from .passport_element_error import PassportElementError


class PassportElementErrorFrontSide(PassportElementError):
    """
    Represents an issue with the front side of a document. The error is considered resolved when the file with the front side of the document changes.

    Source: https://core.telegram.org/bots/api#passportelementerrorfrontside
    """

    source: str = Field("front_side", const=True)
    """Error source, must be *front_side*"""
    type: str
    """The section of the user's Telegram Passport which has the issue, one of 'passport', 'driver_license', 'identity_card', 'internal_passport'"""
    file_hash: str
    """Base64-encoded hash of the file with the front side of the document"""
    message: str
    """Error message"""
