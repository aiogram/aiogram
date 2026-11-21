from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .message_entity import MessageEntity
    from .rich_text_union import RichTextUnion


class TextQuote(TelegramObject):
    """
    This object contains information about the quoted part of a message that is replied to by the given message.

    Source: https://core.telegram.org/bots/api#textquote
    """

    text: str
    """Text of the quoted part of a message that is replied to by the given message; may be empty if the quote was chosen from a rich message"""
    position: int
    """Approximate quote position in the original message in UTF-16 code units as specified by the sender. For quotes from rich messages, it is the position in the text formed by joining plain texts of all quotable texts of the message, separated by line feeds"""
    entities: list[MessageEntity] | None = None
    """*Optional*. Special entities that appear in the quote. Currently, only *bold*, *italic*, *underline*, *strikethrough*, *spoiler*, *custom_emoji*, and *date_time* entities are kept in quotes"""
    is_manual: bool | None = None
    """*Optional*. :code:`True`, if the quote was chosen manually by the message sender. Otherwise, the quote was added automatically by the server"""
    rich_texts: list[RichTextUnion] | None = None
    """*Optional*. Rich text of the quote if it was chosen from a `rich message <https://core.telegram.org/bots/api#richmessage>`_. May contain only plain text, :class:`aiogram.types.rich_text_bold.RichTextBold`, :class:`aiogram.types.rich_text_italic.RichTextItalic`, :class:`aiogram.types.rich_text_underline.RichTextUnderline`, :class:`aiogram.types.rich_text_strikethrough.RichTextStrikethrough`, :class:`aiogram.types.rich_text_spoiler.RichTextSpoiler`, :class:`aiogram.types.rich_text_subscript.RichTextSubscript`, :class:`aiogram.types.rich_text_superscript.RichTextSuperscript`, :class:`aiogram.types.rich_text_date_time.RichTextDateTime`, :class:`aiogram.types.rich_text_custom_emoji.RichTextCustomEmoji`, :class:`aiogram.types.rich_text_mathematical_expression.RichTextMathematicalExpression`, and arrays of them"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            text: str,
            position: int,
            entities: list[MessageEntity] | None = None,
            is_manual: bool | None = None,
            rich_texts: list[RichTextUnion] | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                text=text,
                position=position,
                entities=entities,
                is_manual=is_manual,
                rich_texts=rich_texts,
                **__pydantic_kwargs,
            )
