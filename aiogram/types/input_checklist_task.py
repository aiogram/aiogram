from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .message_entity import MessageEntity


class InputChecklistTask(TelegramObject):
    """
    Describes a task to add to a checklist.

    Source: https://core.telegram.org/bots/api#inputchecklisttask
    """

    id: int
    """Unique identifier of the task; must be positive and unique among all task identifiers currently present in the checklist"""
    text: str
    """Text of the task; 1-100 characters after entities parsing"""
    parse_mode: Optional[str] = None
    """Optional. Mode for parsing entities in the text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    text_entities: Optional[list[MessageEntity]] = None
    """*Optional*. List of special entities that appear in the text, which can be specified instead of parse_mode. Currently, only *bold*, *italic*, *underline*, *strikethrough*, *spoiler*, and *custom_emoji* entities are allowed."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: int,
            text: str,
            parse_mode: Optional[str] = None,
            text_entities: Optional[list[MessageEntity]] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                id=id,
                text=text,
                parse_mode=parse_mode,
                text_entities=text_entities,
                **__pydantic_kwargs,
            )
