from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .base import UNSET_DISABLE_WEB_PAGE_PREVIEW, UNSET_PARSE_MODE
from .input_message_content import InputMessageContent

if TYPE_CHECKING:
    from .message_entity import MessageEntity


class InputTextMessageContent(InputMessageContent):
    """
    Represents the `content <https://core.telegram.org/bots/api#inputmessagecontent>`_ of a text message to be sent as the result of an inline query.

    Source: https://core.telegram.org/bots/api#inputtextmessagecontent
    """

    message_text: str
    """Text of the message to be sent, 1-4096 characters"""
    parse_mode: Optional[str] = UNSET_PARSE_MODE
    """*Optional*. Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    entities: Optional[List[MessageEntity]] = None
    """*Optional*. List of special entities that appear in message text, which can be specified instead of *parse_mode*"""
    disable_web_page_preview: Optional[bool] = UNSET_DISABLE_WEB_PAGE_PREVIEW
    """*Optional*. Disables link previews for links in the sent message"""
