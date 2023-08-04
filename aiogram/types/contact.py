from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

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
    """*Optional*. Contact's user identifier in Telegram. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier."""
    vcard: Optional[str] = None
    """*Optional*. Additional data about the contact in the form of a `vCard <https://en.wikipedia.org/wiki/VCard>`_"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            phone_number: str,
            first_name: str,
            last_name: Optional[str] = None,
            user_id: Optional[int] = None,
            vcard: Optional[str] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                user_id=user_id,
                vcard=vcard,
                **__pydantic_kwargs,
            )
