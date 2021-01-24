from __future__ import annotations

from typing import Optional

from .base import TelegramObject


class Contact(TelegramObject):
    """
    This object represents a phone contact.

    Source: https://core.telegram.org/bots/api#contact
    """

    phone_number: str
    """Contact's phone number"""
    first_name: str
    """Contact's first name"""
    last_name: Optional[str] = None
    """*Optional*. Contact's last name"""
    user_id: Optional[int] = None
    """*Optional*. Contact's user identifier in Telegram"""
    vcard: Optional[str] = None
    """*Optional*. Additional data about the contact in the form of a `vCard <https://en.wikipedia.org/wiki/VCard>`_"""
