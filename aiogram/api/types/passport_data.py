from __future__ import annotations

from typing import TYPE_CHECKING, List

from .base import TelegramObject

if TYPE_CHECKING:
    from .encrypted_credentials import EncryptedCredentials
    from .encrypted_passport_element import EncryptedPassportElement


class PassportData(TelegramObject):
    """
    Contains information about Telegram Passport data shared with the bot by the user.

    Source: https://core.telegram.org/bots/api#passportdata
    """

    data: List[EncryptedPassportElement]
    """Array with information about documents and other Telegram Passport elements that was shared with the bot"""
    credentials: EncryptedCredentials
    """Encrypted credentials required to decrypt the data"""
