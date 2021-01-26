from __future__ import annotations

from typing import List

from pydantic import Field

from .passport_element_error import PassportElementError


class PassportElementErrorFiles(PassportElementError):
    """
    Represents an issue with a list of scans. The error is considered resolved when the list of files containing the scans changes.

    Source: https://core.telegram.org/bots/api#passportelementerrorfiles
    """

    source: str = Field("files", const=True)
    """Error source, must be *files*"""
    type: str
    """The section of the user's Telegram Passport which has the issue, one of 'utility_bill', 'bank_statement', 'rental_agreement', 'passport_registration', 'temporary_registration'"""
    file_hashes: List[str]
    """List of base64-encoded file hashes"""
    message: str
    """Error message"""
