from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import Field

from .inline_query_result import InlineQueryResult

if TYPE_CHECKING:
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_message_content import InputMessageContent


class InlineQueryResultCachedSticker(InlineQueryResult):
    """
    Represents a link to a sticker stored on the Telegram servers. By default, this sticker will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the sticker.
    **Note:** This will only work in Telegram versions released after 9 April, 2016 for static stickers and after 06 July, 2019 for `animated stickers <https://telegram.org/blog/animated-stickers>`_. Older clients will ignore them.

    Source: https://core.telegram.org/bots/api#inlinequeryresultcachedsticker
    """

    type: str = Field("sticker", const=True)
    """Type of the result, must be *sticker*"""
    id: str
    """Unique identifier for this result, 1-64 bytes"""
    sticker_file_id: str
    """A valid file identifier of the sticker"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. `Inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_ attached to the message"""
    input_message_content: Optional[InputMessageContent] = None
    """*Optional*. Content of the message to be sent instead of the sticker"""
