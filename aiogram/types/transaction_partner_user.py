from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

from ..enums import TransactionPartnerType
from .transaction_partner import TransactionPartner

if TYPE_CHECKING:
    from .affiliate_info import AffiliateInfo
    from .gift import Gift
    from .paid_media_union import PaidMediaUnion
    from .user import User


class TransactionPartnerUser(TransactionPartner):
    """
    Describes a transaction with a user.

    Source: https://core.telegram.org/bots/api#transactionpartneruser
    """

    type: Literal[TransactionPartnerType.USER] = TransactionPartnerType.USER
    """Type of the transaction partner, always 'user'"""
    user: User
    """Information about the user"""
    affiliate: Optional[AffiliateInfo] = None
    """*Optional*. Information about the affiliate that received a commission via this transaction"""
    invoice_payload: Optional[str] = None
    """*Optional*. Bot-specified invoice payload"""
    subscription_period: Optional[int] = None
    """*Optional*. The duration of the paid subscription"""
    paid_media: Optional[list[PaidMediaUnion]] = None
    """*Optional*. Information about the paid media bought by the user"""
    paid_media_payload: Optional[str] = None
    """*Optional*. Bot-specified paid media payload"""
    gift: Optional[Gift] = None
    """*Optional*. The gift sent to the user by the bot"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[TransactionPartnerType.USER] = TransactionPartnerType.USER,
            user: User,
            affiliate: Optional[AffiliateInfo] = None,
            invoice_payload: Optional[str] = None,
            subscription_period: Optional[int] = None,
            paid_media: Optional[list[PaidMediaUnion]] = None,
            paid_media_payload: Optional[str] = None,
            gift: Optional[Gift] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type,
                user=user,
                affiliate=affiliate,
                invoice_payload=invoice_payload,
                subscription_period=subscription_period,
                paid_media=paid_media,
                paid_media_payload=paid_media_payload,
                gift=gift,
                **__pydantic_kwargs,
            )
