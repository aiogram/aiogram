from typing import TYPE_CHECKING, Any

from .base import TelegramObject


class Widget(TelegramObject):
    """
    This object describes an `HTML widget <https://core.telegram.org/bots/widgets>`_.

    Source: https://core.telegram.org/bots/api#widget
    """

    html: str
    """HTML code of the widget"""
    id: str | None = None
    """*Optional*. Unique identifier of the shared widget, which can be used to send the widget again using the method :class:`aiogram.methods.send_shared_widget.SendSharedWidget`; omitted if the widget isn't shared"""
    width: int | None = None
    """*Optional*. Width of the widget in logical pixels; omitted if the widget must occupy the whole width of the message bubble"""
    height: int | None = None
    """*Optional*. Height of the widget in logical pixels; omitted if the height of the widget isn't fixed"""
    public_data: str | None = None
    """*Optional*. Public data of the widget, which is available wherever the widget is shown. All messages with a shared widget have the same public data"""
    chat_data: str | None = None
    """*Optional*. Data of the widget, which is specific to the message"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            html: str,
            id: str | None = None,
            width: int | None = None,
            height: int | None = None,
            public_data: str | None = None,
            chat_data: str | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                html=html,
                id=id,
                width=width,
                height=height,
                public_data=public_data,
                chat_data=chat_data,
                **__pydantic_kwargs,
            )
