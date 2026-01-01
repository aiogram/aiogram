from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ..types import MessageEntity
from .base import TelegramMethod


class SendMessageDraft(TelegramMethod[bool]):
    """
    Use this method to stream a partial message to a user while the message is being generated; supported only for bots with forum topic mode enabled. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#sendmessagedraft
    """

    __returning__ = bool
    __api_method__ = "sendMessageDraft"

    chat_id: int
    """Unique identifier for the target private chat"""
    draft_id: int
    """Unique identifier of the message draft; must be non-zero. Changes of drafts with the same identifier are animated"""
    text: str
    """Text of the message to be sent, 1-4096 characters after entities parsing"""
    message_thread_id: Optional[int] = None
    """Unique identifier for the target message thread"""
    parse_mode: Optional[str] = None
    """Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    entities: Optional[list[MessageEntity]] = None
    """A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: int,
            draft_id: int,
            text: str,
            message_thread_id: Optional[int] = None,
            parse_mode: Optional[str] = None,
            entities: Optional[list[MessageEntity]] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                draft_id=draft_id,
                text=text,
                message_thread_id=message_thread_id,
                parse_mode=parse_mode,
                entities=entities,
                **__pydantic_kwargs,
            )
