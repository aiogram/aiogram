from __future__ import annotations

from .base import TelegramObject


class EncryptedCredentials(TelegramObject):
    """
    Contains data required for decrypting and authenticating :class:`aiogram.types.encrypted_passport_element.EncryptedPassportElement`. See the `Telegram Passport Documentation <https://core.telegram.org/passport#receiving-information>`_ for a complete description of the data decryption and authentication processes.

    Source: https://core.telegram.org/bots/api#encryptedcredentials
    """

    data: str
    """Base64-encoded encrypted JSON-serialized data with unique user's payload, data hashes and secrets required for :class:`aiogram.types.encrypted_passport_element.EncryptedPassportElement` decryption and authentication"""
    hash: str
    """Base64-encoded data hash for data authentication"""
    secret: str
    """Base64-encoded secret, encrypted with the bot's public RSA key, required for data decryption"""
