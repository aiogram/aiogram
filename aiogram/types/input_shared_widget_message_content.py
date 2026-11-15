from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client.default import Default
from .input_message_content import InputMessageContent

if TYPE_CHECKING:
    from .message_entity import MessageEntity


class InputSharedWidgetMessageContent(InputMessageContent):
    """
    Represents the `content <https://core.telegram.org/bots/api#inputmessagecontent>`_ of a message with a shared widget to be sent as the result of an inline query. Currently, widgets can't be sent in response to inline queries in the production environment.

    Source: https://core.telegram.org/bots/api#inputsharedwidgetmessagecontent
    """

    widget_id: str
    """Unique identifier of the shared widget created by the bot"""
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

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            widget_id: str,
            chat_data: str | None = None,
            caption: str | None = None,
            parse_mode: str | Default | None = Default("parse_mode"),
            caption_entities: list[MessageEntity] | None = None,
            show_caption_above_media: bool | Default | None = Default("show_caption_above_media"),
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                widget_id=widget_id,
                chat_data=chat_data,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                show_caption_above_media=show_caption_above_media,
                **__pydantic_kwargs,
            )
