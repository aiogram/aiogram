from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .gift import Gift
    from .message_entity import MessageEntity


class GiftInfo(TelegramObject):
    """
    Describes a service message about a regular gift that was sent or received.

    Source: https://core.telegram.org/bots/api#giftinfo
    """

    gift: Gift
    """Information about the gift"""
    owned_gift_id: Optional[str] = None
    """*Optional*. Unique identifier of the received gift for the bot; only present for gifts received on behalf of business accounts"""
    convert_star_count: Optional[int] = None
    """*Optional*. Number of Telegram Stars that can be claimed by the receiver by converting the gift; omitted if conversion to Telegram Stars is impossible"""
    prepaid_upgrade_star_count: Optional[int] = None
    """*Optional*. Number of Telegram Stars that were prepaid by the sender for the ability to upgrade the gift"""
    can_be_upgraded: Optional[bool] = None
    """*Optional*. :code:`True`, if the gift can be upgraded to a unique gift"""
    text: Optional[str] = None
    """*Optional*. Text of the message that was added to the gift"""
    entities: Optional[list[MessageEntity]] = None
    """*Optional*. Special entities that appear in the text"""
    is_private: Optional[bool] = None
    """*Optional*. :code:`True`, if the sender and gift text are shown only to the gift receiver; otherwise, everyone will be able to see them"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            gift: Gift,
            owned_gift_id: Optional[str] = None,
            convert_star_count: Optional[int] = None,
            prepaid_upgrade_star_count: Optional[int] = None,
            can_be_upgraded: Optional[bool] = None,
            text: Optional[str] = None,
            entities: Optional[list[MessageEntity]] = None,
            is_private: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                gift=gift,
                owned_gift_id=owned_gift_id,
                convert_star_count=convert_star_count,
                prepaid_upgrade_star_count=prepaid_upgrade_star_count,
                can_be_upgraded=can_be_upgraded,
                text=text,
                entities=entities,
                is_private=is_private,
                **__pydantic_kwargs,
            )
