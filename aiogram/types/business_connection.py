from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject
from .custom import DateTime

if TYPE_CHECKING:
    from .user import User


class BusinessConnection(TelegramObject):
    """
    Describes the connection of the bot with a business account.

    Source: https://core.telegram.org/bots/api#businessconnection
    """

    id: str
    """Unique identifier of the business connection"""
    user: User
    """Business account user that created the business connection"""
    user_chat_id: int
    """Identifier of a private chat with the user who created the business connection. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier."""
    date: DateTime
    """Date the connection was established in Unix time"""
    can_reply: bool
    """True, if the bot can act on behalf of the business account in chats that were active in the last 24 hours"""
    is_enabled: bool
    """True, if the connection is active"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: str,
            user: User,
            user_chat_id: int,
            date: DateTime,
            can_reply: bool,
            is_enabled: bool,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                id=id,
                user=user,
                user_chat_id=user_chat_id,
                date=date,
                can_reply=can_reply,
                is_enabled=is_enabled,
                **__pydantic_kwargs,
            )
