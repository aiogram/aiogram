from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from .paid_media import PaidMedia

if TYPE_CHECKING:
    from .video import Video


class PaidMediaVideo(PaidMedia):
    """
    The paid media is a video.

    Source: https://core.telegram.org/bots/api#paidmediavideo
    """

    type: Literal["video"] = "video"
    """Type of the paid media, always 'video'"""
    video: Video
    """The video"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            type: Literal["video"] = "video",
            video: Video,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(type=type, video=video, **__pydantic_kwargs)
