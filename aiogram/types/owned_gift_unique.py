from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

from aiogram.enums import OwnedGiftType

from .owned_gift import OwnedGift

if TYPE_CHECKING:
    from .unique_gift import UniqueGift
    from .user import User


class OwnedGiftUnique(OwnedGift):
    """
    Describes a unique gift received and owned by a user or a chat.

    Source: https://core.telegram.org/bots/api#ownedgiftunique
    """

    type: Literal[OwnedGiftType.UNIQUE] = OwnedGiftType.UNIQUE
    """Type of the gift, always 'unique'"""
    gift: UniqueGift
    """Information about the unique gift"""
    send_date: int
    """Date the gift was sent in Unix time"""
    owned_gift_id: Optional[str] = None
    """*Optional*. Unique identifier of the received gift for the bot; for gifts received on behalf of business accounts only"""
    sender_user: Optional[User] = None
    """*Optional*. Sender of the gift if it is a known user"""
    is_saved: Optional[bool] = None
    """*Optional*. True, if the gift is displayed on the account's profile page; for gifts received on behalf of business accounts only"""
    can_be_transferred: Optional[bool] = None
    """*Optional*. True, if the gift can be transferred to another owner; for gifts received on behalf of business accounts only"""
    transfer_star_count: Optional[int] = None
    """*Optional*. Number of Telegram Stars that must be paid to transfer the gift; omitted if the bot cannot transfer the gift"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[OwnedGiftType.UNIQUE] = OwnedGiftType.UNIQUE,
            gift: UniqueGift,
            send_date: int,
            owned_gift_id: Optional[str] = None,
            sender_user: Optional[User] = None,
            is_saved: Optional[bool] = None,
            can_be_transferred: Optional[bool] = None,
            transfer_star_count: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                gift=gift,
                send_date=send_date,
                owned_gift_id=owned_gift_id,
                sender_user=sender_user,
                is_saved=is_saved,
                can_be_transferred=can_be_transferred,
                transfer_star_count=transfer_star_count,
                **__pydantic_kwargs,
            )
