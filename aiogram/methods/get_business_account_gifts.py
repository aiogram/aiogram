from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ..types import OwnedGifts
from .base import TelegramMethod


class GetBusinessAccountGifts(TelegramMethod[OwnedGifts]):
    """
    Returns the gifts received and owned by a managed business account. Requires the *can_view_gifts_and_stars* business bot right. Returns :class:`aiogram.types.owned_gifts.OwnedGifts` on success.

    Source: https://core.telegram.org/bots/api#getbusinessaccountgifts
    """

    __returning__ = OwnedGifts
    __api_method__ = "getBusinessAccountGifts"

    business_connection_id: str
    """Unique identifier of the business connection"""
    exclude_unsaved: Optional[bool] = None
    """Pass True to exclude gifts that aren't saved to the account's profile page"""
    exclude_saved: Optional[bool] = None
    """Pass True to exclude gifts that are saved to the account's profile page"""
    exclude_unlimited: Optional[bool] = None
    """Pass True to exclude gifts that can be purchased an unlimited number of times"""
    exclude_limited: Optional[bool] = None
    """Pass True to exclude gifts that can be purchased a limited number of times"""
    exclude_unique: Optional[bool] = None
    """Pass True to exclude unique gifts"""
    sort_by_price: Optional[bool] = None
    """Pass True to sort results by gift price instead of send date. Sorting is applied before pagination."""
    offset: Optional[str] = None
    """Offset of the first entry to return as received from the previous request; use empty string to get the first chunk of results"""
    limit: Optional[int] = None
    """The maximum number of gifts to be returned; 1-100. Defaults to 100"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            business_connection_id: str,
            exclude_unsaved: Optional[bool] = None,
            exclude_saved: Optional[bool] = None,
            exclude_unlimited: Optional[bool] = None,
            exclude_limited: Optional[bool] = None,
            exclude_unique: Optional[bool] = None,
            sort_by_price: Optional[bool] = None,
            offset: Optional[str] = None,
            limit: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                business_connection_id=business_connection_id,
                exclude_unsaved=exclude_unsaved,
                exclude_saved=exclude_saved,
                exclude_unlimited=exclude_unlimited,
                exclude_limited=exclude_limited,
                exclude_unique=exclude_unique,
                sort_by_price=sort_by_price,
                offset=offset,
                limit=limit,
                **__pydantic_kwargs,
            )
