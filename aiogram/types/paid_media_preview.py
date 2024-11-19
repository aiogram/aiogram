from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional

from ..enums import PaidMediaType
from .paid_media import PaidMedia


class PaidMediaPreview(PaidMedia):
    """
    The paid media isn't available before the payment.

    Source: https://core.telegram.org/bots/api#paidmediapreview
    """

    type: Literal[PaidMediaType.PREVIEW] = PaidMediaType.PREVIEW
    """Type of the paid media, always 'preview'"""
    width: Optional[int] = None
    """*Optional*. Media width as defined by the sender"""
    height: Optional[int] = None
    """*Optional*. Media height as defined by the sender"""
    duration: Optional[int] = None
    """*Optional*. Duration of the media in seconds as defined by the sender"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal[PaidMediaType.PREVIEW] = PaidMediaType.PREVIEW,
            width: Optional[int] = None,
            height: Optional[int] = None,
            duration: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                type=type, width=width, height=height, duration=duration, **__pydantic_kwargs
            )
