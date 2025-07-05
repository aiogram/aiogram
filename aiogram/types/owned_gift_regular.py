from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

from aiogram.enums import OwnedGiftType

from .owned_gift import OwnedGift

if TYPE_CHECKING:
    from .gift import Gift
    from .message_entity import MessageEntity
    from .user import User


class OwnedGiftRegular(OwnedGift):
    """
    Describes a regular gift owned by a user or a chat.

    Source: https://core.telegram.org/bots/api#ownedgiftregular
    """

    type: Literal[OwnedGiftType.REGULAR] = OwnedGiftType.REGULAR
    """Type of the gift, always 'regular'"""
    gift: Gift
    """Information about the regular gift"""
    send_date: int
    """Date the gift was sent in Unix time"""
    owned_gift_id: Optional[str] = None
    """*Optional*. Unique identifier of the gift for the bot; for gifts received on behalf of business accounts only"""
    sender_user: Optional[User] = None
    """*Optional*. Sender of the gift if it is a known user"""
    text: Optional[str] = None
    """*Optional*. Text of the message that was added to the gift"""
    entities: Optional[list[MessageEntity]] = None
    """*Optional*. Special entities that appear in the text"""
    is_private: Optional[bool] = None
    """*Optional*. :code:`True`, if the sender and gift text are shown only to the gift receiver; otherwise, everyone will be able to see them"""
    is_saved: Optional[bool] = None
    """*Optional*. :code:`True`, if the gift is displayed on the account's profile page; for gifts received on behalf of business accounts only"""
    can_be_upgraded: Optional[bool] = None
    """*Optional*. :code:`True`, if the gift can be upgraded to a unique gift; for gifts received on behalf of business accounts only"""
    was_refunded: Optional[bool] = None
    """*Optional*. :code:`True`, if the gift was refunded and isn't available anymore"""
    convert_star_count: Optional[int] = None
    """*Optional*. Number of Telegram Stars that can be claimed by the receiver instead of the gift; omitted if the gift cannot be converted to Telegram Stars"""
    prepaid_upgrade_star_count: Optional[int] = None
    """*Optional*. Number of Telegram Stars that were paid by the sender for the ability to upgrade the gift"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[OwnedGiftType.REGULAR] = OwnedGiftType.REGULAR,
            gift: Gift,
            send_date: int,
            owned_gift_id: Optional[str] = None,
            sender_user: Optional[User] = None,
            text: Optional[str] = None,
            entities: Optional[list[MessageEntity]] = None,
            is_private: Optional[bool] = None,
            is_saved: Optional[bool] = None,
            can_be_upgraded: Optional[bool] = None,
            was_refunded: Optional[bool] = None,
            convert_star_count: Optional[int] = None,
            prepaid_upgrade_star_count: Optional[int] = None,
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
                text=text,
                entities=entities,
                is_private=is_private,
                is_saved=is_saved,
                can_be_upgraded=can_be_upgraded,
                was_refunded=was_refunded,
                convert_star_count=convert_star_count,
                prepaid_upgrade_star_count=prepaid_upgrade_star_count,
                **__pydantic_kwargs,
            )
