from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .unique_gift import UniqueGift


class UniqueGiftInfo(TelegramObject):
    """
    Describes a service message about a unique gift that was sent or received.

    Source: https://core.telegram.org/bots/api#uniquegiftinfo
    """

    gift: UniqueGift
    """Information about the gift"""
    origin: str
    """Origin of the gift. Currently, either 'upgrade' or 'transfer'"""
    owned_gift_id: Optional[str] = None
    """*Optional*. Unique identifier of the received gift for the bot; only present for gifts received on behalf of business accounts"""
    transfer_star_count: Optional[int] = None
    """*Optional*. Number of Telegram Stars that must be paid to transfer the gift; omitted if the bot cannot transfer the gift"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            gift: UniqueGift,
            origin: str,
            owned_gift_id: Optional[str] = None,
            transfer_star_count: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                gift=gift,
                origin=origin,
                owned_gift_id=owned_gift_id,
                transfer_star_count=transfer_star_count,
                **__pydantic_kwargs,
            )
