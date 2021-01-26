from __future__ import annotations

from pydantic import Field

from .passport_element_error import PassportElementError


class PassportElementErrorUnspecified(PassportElementError):
    """
    Represents an issue in an unspecified place. The error is considered resolved when new data is added.

    Source: https://core.telegram.org/bots/api#passportelementerrorunspecified
    """

    source: str = Field("unspecified", const=True)
    """Error source, must be *unspecified*"""
    type: str
    """Type of element of the user's Telegram Passport which has the issue"""
    element_hash: str
    """Base64-encoded element hash"""
    message: str
    """Error message"""
