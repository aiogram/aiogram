from typing import TYPE_CHECKING, Any

from ..client.default import Default
from ..types import (
    ChatIdUnion,
    InlineKeyboardMarkup,
    InputRichMessage,
    LinkPreviewOptions,
    MessageEntity,
)
from .base import TelegramMethod


class EditEphemeralMessageText(TelegramMethod[bool]):
    """
    Use this method to edit an ephemeral text or rich message. Note that it is not guaranteed that the user will receive the message edit event, especially if they are offline. On success, :code:`True` is returned.

    Source: https://core.telegram.org/bots/api#editephemeralmessagetext
    """

    __returning__ = bool
    __api_method__ = "editEphemeralMessageText"

    chat_id: ChatIdUnion
    """Unique identifier for the target chat or username of the target supergroup in the format :code:`@username`"""
    receiver_user_id: int
    """Identifier of the user who received the message"""
    ephemeral_message_id: int
    """Identifier of the ephemeral message to edit"""
    text: str | None = None
    """New text of the message, 1-4096 characters after entity parsing; required if *rich_message* isn't specified"""
    parse_mode: str | Default | None = Default("parse_mode")
    """Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details"""
    entities: list[MessageEntity] | None = None
    """A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*"""
    link_preview_options: LinkPreviewOptions | Default | None = Default("link_preview")
    """Link preview generation options for the message"""
    reply_markup: InlineKeyboardMarkup | None = None
    """A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_"""
    rich_message: InputRichMessage | None = None
    """New rich content of the message; required if *text* isn't specified"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: ChatIdUnion,
            receiver_user_id: int,
            ephemeral_message_id: int,
            text: str | None = None,
            parse_mode: str | Default | None = Default("parse_mode"),
            entities: list[MessageEntity] | None = None,
            link_preview_options: LinkPreviewOptions | Default | None = Default("link_preview"),
            reply_markup: InlineKeyboardMarkup | None = None,
            rich_message: InputRichMessage | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                receiver_user_id=receiver_user_id,
                ephemeral_message_id=ephemeral_message_id,
                text=text,
                parse_mode=parse_mode,
                entities=entities,
                link_preview_options=link_preview_options,
                reply_markup=reply_markup,
                rich_message=rich_message,
                **__pydantic_kwargs,
            )
