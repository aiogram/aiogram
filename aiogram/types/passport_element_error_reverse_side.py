from __future__ import annotations

from pydantic import Field

from .passport_element_error import PassportElementError


class PassportElementErrorReverseSide(PassportElementError):
    """
    Represents an issue with the reverse side of a document. The error is considered resolved when the file with reverse side of the document changes.

    Source: https://core.telegram.org/bots/api#passportelementerrorreverseside
    """

    source: str = Field("reverse_side", const=True)
    """Error source, must be *reverse_side*"""
    type: str
    """The section of the user's Telegram Passport which has the issue, one of 'driver_license', 'identity_card'"""
    file_hash: str
    """Base64-encoded hash of the file with the reverse side of the document"""
    message: str
    """Error message"""
