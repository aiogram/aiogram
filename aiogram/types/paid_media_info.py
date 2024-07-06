from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Union

from .base import TelegramObject

if TYPE_CHECKING:
    from .paid_media_photo import PaidMediaPhoto
    from .paid_media_preview import PaidMediaPreview
    from .paid_media_video import PaidMediaVideo


class PaidMediaInfo(TelegramObject):
    """
    Describes the paid media added to a message.

    Source: https://core.telegram.org/bots/api#paidmediainfo
    """

    star_count: int
    """The number of Telegram Stars that must be paid to buy access to the media"""
    paid_media: List[Union[PaidMediaPreview, PaidMediaPhoto, PaidMediaVideo]]
    """Information about the paid media"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            star_count: int,
            paid_media: List[Union[PaidMediaPreview, PaidMediaPhoto, PaidMediaVideo]],
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(star_count=star_count, paid_media=paid_media, **__pydantic_kwargs)
