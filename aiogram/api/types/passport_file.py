from __future__ import annotations

from .base import TelegramObject


class PassportFile(TelegramObject):
    """
    This object represents a file uploaded to Telegram Passport. Currently all Telegram Passport files are in JPEG format when decrypted and don't exceed 10MB.

    Source: https://core.telegram.org/bots/api#passportfile
    """

    file_id: str
    """Identifier for this file"""
    file_size: int
    """File size"""
    file_date: int
    """Unix time when the file was uploaded"""
