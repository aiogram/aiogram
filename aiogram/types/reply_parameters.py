from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client.default import Default
from .base import TelegramObject

if TYPE_CHECKING:
    from .chat_id_union import ChatIdUnion
    from .message_entity import MessageEntity
    from .rich_text_union import RichTextUnion


class ReplyParameters(TelegramObject):
    """
    Describes reply parameters for the message that is being sent.

    Source: https://core.telegram.org/bots/api#replyparameters
    """

    message_id: int | None = None
    """*Optional*. Identifier of the message that will be replied to in the current chat, or in the chat *chat_id* if it is specified. Required if *ephemeral_message_id* isn't specified"""
    chat_id: ChatIdUnion | None = None
    """*Optional*. If the message to be replied to is from a different chat, unique identifier for the chat or username of the bot, supergroup, or channel in the format :code:`@username`. Not supported for messages sent on behalf of a business account, messages from channel direct messages chats and ephemeral messages"""
    allow_sending_without_reply: bool | Default | None = Default("allow_sending_without_reply")
    """*Optional*. Pass :code:`True` if the message should be sent even if the specified message to be replied to is not found. Always :code:`False` for replies in another chat or forum topic, and sent ephemeral messages. Always :code:`True` for messages sent on behalf of a business account"""
    quote: str | None = None
    """*Optional*. Quoted part of the message to be replied to; 0-1024 characters after entities parsing. The quote must be an exact substring of the message to be replied to, including *bold*, *italic*, *underline*, *strikethrough*, *spoiler*, *custom_emoji*, and *date_time* entities. The message will fail to send if the quote isn't found in the original message. Ignored for ephemeral messages"""
    quote_parse_mode: str | Default | None = Default("parse_mode")
    """*Optional*. Mode for parsing entities in the quote. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details"""
    quote_entities: list[MessageEntity] | None = None
    """*Optional*. A JSON-serialized list of special entities that appear in the quote. It can be specified instead of *quote_parse_mode*"""
    quote_position: int | None = None
    """*Optional*. Position of the quote in the original message in UTF-16 code units. For quotes from rich messages, it is the position in the text formed by joining plain texts of all quotable texts of the message, separated by line feeds"""
    checklist_task_id: int | None = None
    """*Optional*. Identifier of the specific checklist task to be replied to"""
    poll_option_id: str | None = None
    """*Optional*. Persistent identifier of the specific poll option to be replied to"""
    ephemeral_message_id: int | None = None
    """*Optional*. Identifier of the incoming ephemeral message that will be replied to in the current chat. A reply to an ephemeral message must itself be an ephemeral message. An ephemeral message may only be replied to within 15 seconds of being sent. Required if *message_id* isn't specified"""
    quote_rich_texts: list[RichTextUnion] | None = None
    """*Optional*. A JSON-serialized list of quoted parts of the `rich message <https://core.telegram.org/bots/api#richmessage>`_ to be replied to. Must contain one element for each quoted text of the message in the order of their appearance. Each of the following is a separate quoted text: the text of a paragraph, a heading, a preformatted block, a footer, or a mathematical expression; the text and the credit of a block quotation or a pull quotation; the summary of a details block; the caption and each cell of a table; the text and the credit of a caption of a media block, a collage, a slideshow, or a map. Texts of blocks nested in lists, block quotations, details, collages, and slideshows are separate quoted texts too. The first and the last elements can contain only a part of the corresponding text; all other elements must contain the whole text. Formatting of the quoted parts must be kept, and rich texts must be nested in the same way as in the message received from the server. Mathematical expressions must be quoted entirely. Buttons in :class:`aiogram.types.rich_block_buttons.RichBlockButtons`, anchors and dividers can't be quoted. Up to 32 quoted texts with total length up to 1024 characters can be specified. Only plain text, :class:`aiogram.types.rich_text_bold.RichTextBold`, :class:`aiogram.types.rich_text_italic.RichTextItalic`, :class:`aiogram.types.rich_text_underline.RichTextUnderline`, :class:`aiogram.types.rich_text_strikethrough.RichTextStrikethrough`, :class:`aiogram.types.rich_text_spoiler.RichTextSpoiler`, :class:`aiogram.types.rich_text_subscript.RichTextSubscript`, :class:`aiogram.types.rich_text_superscript.RichTextSuperscript`, :class:`aiogram.types.rich_text_date_time.RichTextDateTime`, :class:`aiogram.types.rich_text_custom_emoji.RichTextCustomEmoji`, :class:`aiogram.types.rich_text_mathematical_expression.RichTextMathematicalExpression`, and arrays of them are kept in the quote; other rich text types are replaced with their text. If non-empty, then *quote*, *quote_parse_mode* and *quote_entities* are ignored"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            message_id: int | None = None,
            chat_id: ChatIdUnion | None = None,
            allow_sending_without_reply: bool | Default | None = Default(
                "allow_sending_without_reply"
            ),
            quote: str | None = None,
            quote_parse_mode: str | Default | None = Default("parse_mode"),
            quote_entities: list[MessageEntity] | None = None,
            quote_position: int | None = None,
            checklist_task_id: int | None = None,
            poll_option_id: str | None = None,
            ephemeral_message_id: int | None = None,
            quote_rich_texts: list[RichTextUnion] | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                message_id=message_id,
                chat_id=chat_id,
                allow_sending_without_reply=allow_sending_without_reply,
                quote=quote,
                quote_parse_mode=quote_parse_mode,
                quote_entities=quote_entities,
                quote_position=quote_position,
                checklist_task_id=checklist_task_id,
                poll_option_id=poll_option_id,
                ephemeral_message_id=ephemeral_message_id,
                quote_rich_texts=quote_rich_texts,
                **__pydantic_kwargs,
            )
