from typing import TYPE_CHECKING, Any

from .base import TelegramMethod


class EditSharedWidgetData(TelegramMethod[bool]):
    """
    Use this method to edit public data of a shared widget created by the bot. A shared widget can be edited at most once per second. On success, :code:`True` is returned.

    Source: https://core.telegram.org/bots/api#editsharedwidgetdata
    """

    __returning__ = bool
    __api_method__ = "editSharedWidgetData"

    widget_id: str
    """Unique identifier of the shared widget"""
    public_data: str
    """New public data of the widget, 0-1024 bytes; pass an empty string to remove the public data"""
    cache_time: int | None = None
    """The maximum amount of time in seconds that the public data of the widget may be cached client-side; 5-3600. If omitted, then the current value is kept, which is 30 by default"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            widget_id: str,
            public_data: str,
            cache_time: int | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                widget_id=widget_id,
                public_data=public_data,
                cache_time=cache_time,
                **__pydantic_kwargs,
            )
