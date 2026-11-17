from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client.default import Default
from .input_message_content import InputMessageContent

if TYPE_CHECKING:
    from .message_entity import MessageEntity


class InputWidgetMessageContent(InputMessageContent):
    """
    Represents the `content <https://core.telegram.org/bots/api#inputmessagecontent>`_ of a message with an `HTML widget <https://core.telegram.org/bots/widgets>`_ to be sent as the result of an inline query. Currently, widgets can't be sent in response to inline queries in the production environment.

    Source: https://core.telegram.org/bots/api#inputwidgetmessagecontent
    """

    html: str
    """HTML code of the widget, 1-32768 bytes. The code must not exceed 4096 bytes when compressed by zlib with the maximum compression level"""
    width: int | None = None
    """*Optional*. Width of the widget in logical pixels; omit if the widget must occupy the whole width of the message bubble. The width is clamped by the app to the range from 200 to the maximum width of the message bubble"""
    height: int | None = None
    """*Optional*. Height of the widget in logical pixels; omit if the height of the widget isn't fixed. The height is clamped by the app to the range 50-600"""
    public_data: str | None = None
    """*Optional*. Public data of the widget, 0-1024 bytes, which will be available wherever the widget is shown. If the widget is shared, then all messages with it will have the same public data"""
    chat_data: str | None = None
    """*Optional*. Data of the widget, which is specific to the message, 0-1024 bytes"""
    caption: str | None = None
    """*Optional*. Widget caption, 0-1024 characters after entities parsing"""
    parse_mode: str | Default | None = Default("parse_mode")
    """*Optional*. Mode for parsing entities in the widget caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details"""
    caption_entities: list[MessageEntity] | None = None
    """*Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    show_caption_above_media: bool | Default | None = Default("show_caption_above_media")
    """*Optional*. Pass :code:`True` if the caption must be shown above the widget"""
    allow_queries: bool | None = None
    """*Optional*. Pass :code:`True` to allow the widget to send queries to the bot"""
    is_shared: bool | None = None
    """*Optional*. Pass :code:`True` to create a shared widget. Each message sent from the result creates a separate shared widget, whose identifier is received by the bot only in the field *widget_id* of queries from the widget. To send an existing shared widget in response to an inline query, use :class:`aiogram.types.input_shared_widget_message_content.InputSharedWidgetMessageContent` instead"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            html: str,
            width: int | None = None,
            height: int | None = None,
            public_data: str | None = None,
            chat_data: str | None = None,
            caption: str | None = None,
            parse_mode: str | Default | None = Default("parse_mode"),
            caption_entities: list[MessageEntity] | None = None,
            show_caption_above_media: bool | Default | None = Default("show_caption_above_media"),
            allow_queries: bool | None = None,
            is_shared: bool | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                html=html,
                width=width,
                height=height,
                public_data=public_data,
                chat_data=chat_data,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                show_caption_above_media=show_caption_above_media,
                allow_queries=allow_queries,
                is_shared=is_shared,
                **__pydantic_kwargs,
            )
