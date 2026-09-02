from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client.default import Default
from ..types import MessageEntity
from .base import TelegramMethod


class SendMessageDraft(TelegramMethod[bool]):
    """
    Use this method to stream a partial message to a user while the message is being generated. Note that the streamed draft is ephemeral and acts as a temporary 30-second preview - once the output is finalized, you **must** call :class:`aiogram.methods.send_message.SendMessage` with the complete message to persist it in the user's chat. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#sendmessagedraft
    """

    __returning__ = bool
    __api_method__ = "sendMessageDraft"

    chat_id: int
    """Unique identifier for the target private chat"""
    draft_id: int
    """Unique identifier of the message draft; must be non-zero. Changes to drafts with the same identifier are animated. Otherwise, the draft is replaced without animation"""
    message_thread_id: int | None = None
    """Unique identifier for the target message thread"""
    text: str | None = None
    """Text of the message to be sent, 0-4096 characters after entities parsing. Pass an empty text to show a 'Thinking…' placeholder"""
    parse_mode: str | Default | None = Default("parse_mode")
    """Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details"""
    entities: list[MessageEntity] | None = None
    """A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*"""
    can_stop: bool | None = None
    """Pass :code:`True` to show the user a button to stop further drafts. The bot will receive an :class:`aiogram.types.update.Update` 'stopped_message_generation' if the user presses the button"""
    keep_on_stop: bool | None = None
    """Pass :code:`True` to keep the draft in the chat when the button is pressed. The draft will still disappear after a short time or if the bot sends a message. To fully preserve the partial draft, the bot should send it as a new message"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: int,
            draft_id: int,
            message_thread_id: int | None = None,
            text: str | None = None,
            parse_mode: str | Default | None = Default("parse_mode"),
            entities: list[MessageEntity] | None = None,
            can_stop: bool | None = None,
            keep_on_stop: bool | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                draft_id=draft_id,
                message_thread_id=message_thread_id,
                text=text,
                parse_mode=parse_mode,
                entities=entities,
                can_stop=can_stop,
                keep_on_stop=keep_on_stop,
                **__pydantic_kwargs,
            )
