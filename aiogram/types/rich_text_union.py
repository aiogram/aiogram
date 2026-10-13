from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, TypeAlias

from pydantic import Discriminator, Tag
from typing_extensions import TypeAliasType

from ..enums import RichTextType
from .rich_text_anchor import RichTextAnchor
from .rich_text_anchor_link import RichTextAnchorLink
from .rich_text_bank_card_number import RichTextBankCardNumber
from .rich_text_bold import RichTextBold
from .rich_text_bot_command import RichTextBotCommand
from .rich_text_button import RichTextButton
from .rich_text_cashtag import RichTextCashtag
from .rich_text_code import RichTextCode
from .rich_text_custom_emoji import RichTextCustomEmoji
from .rich_text_date_time import RichTextDateTime
from .rich_text_email_address import RichTextEmailAddress
from .rich_text_hashtag import RichTextHashtag
from .rich_text_italic import RichTextItalic
from .rich_text_marked import RichTextMarked
from .rich_text_mathematical_expression import RichTextMathematicalExpression
from .rich_text_mention import RichTextMention
from .rich_text_phone_number import RichTextPhoneNumber
from .rich_text_reference import RichTextReference
from .rich_text_reference_link import RichTextReferenceLink
from .rich_text_spoiler import RichTextSpoiler
from .rich_text_strikethrough import RichTextStrikethrough
from .rich_text_subscript import RichTextSubscript
from .rich_text_superscript import RichTextSuperscript
from .rich_text_text_mention import RichTextTextMention
from .rich_text_underline import RichTextUnderline
from .rich_text_url import RichTextUrl

if TYPE_CHECKING:
    RichTextUnion: TypeAlias = (
        str
        | list["RichTextUnion"]
        | RichTextBold
        | RichTextItalic
        | RichTextUnderline
        | RichTextStrikethrough
        | RichTextSpoiler
        | RichTextDateTime
        | RichTextTextMention
        | RichTextSubscript
        | RichTextSuperscript
        | RichTextMarked
        | RichTextCode
        | RichTextCustomEmoji
        | RichTextMathematicalExpression
        | RichTextUrl
        | RichTextEmailAddress
        | RichTextPhoneNumber
        | RichTextBankCardNumber
        | RichTextMention
        | RichTextHashtag
        | RichTextCashtag
        | RichTextBotCommand
        | RichTextButton
        | RichTextAnchor
        | RichTextAnchorLink
        | RichTextReference
        | RichTextReferenceLink
    )
else:

    def _rich_text_union_tag(value: Any) -> Any:
        if isinstance(value, str):
            return "str"
        if isinstance(value, (list, tuple)):
            return "list"
        if isinstance(value, dict):
            return value.get("type")
        return getattr(value, "type", None)

    RichTextUnion = TypeAliasType(
        "RichTextUnion",
        Annotated[
            Annotated[str, Tag("str")]
            | Annotated[list["RichTextUnion"], Tag("list")]
            | Annotated[RichTextBold, Tag(RichTextType.BOLD)]
            | Annotated[RichTextItalic, Tag(RichTextType.ITALIC)]
            | Annotated[RichTextUnderline, Tag(RichTextType.UNDERLINE)]
            | Annotated[RichTextStrikethrough, Tag(RichTextType.STRIKETHROUGH)]
            | Annotated[RichTextSpoiler, Tag(RichTextType.SPOILER)]
            | Annotated[RichTextDateTime, Tag(RichTextType.DATE_TIME)]
            | Annotated[RichTextTextMention, Tag(RichTextType.TEXT_MENTION)]
            | Annotated[RichTextSubscript, Tag(RichTextType.SUBSCRIPT)]
            | Annotated[RichTextSuperscript, Tag(RichTextType.SUPERSCRIPT)]
            | Annotated[RichTextMarked, Tag(RichTextType.MARKED)]
            | Annotated[RichTextCode, Tag(RichTextType.CODE)]
            | Annotated[RichTextCustomEmoji, Tag(RichTextType.CUSTOM_EMOJI)]
            | Annotated[RichTextMathematicalExpression, Tag(RichTextType.MATHEMATICAL_EXPRESSION)]
            | Annotated[RichTextUrl, Tag(RichTextType.URL)]
            | Annotated[RichTextEmailAddress, Tag(RichTextType.EMAIL_ADDRESS)]
            | Annotated[RichTextPhoneNumber, Tag(RichTextType.PHONE_NUMBER)]
            | Annotated[RichTextBankCardNumber, Tag(RichTextType.BANK_CARD_NUMBER)]
            | Annotated[RichTextMention, Tag(RichTextType.MENTION)]
            | Annotated[RichTextHashtag, Tag(RichTextType.HASHTAG)]
            | Annotated[RichTextCashtag, Tag(RichTextType.CASHTAG)]
            | Annotated[RichTextBotCommand, Tag(RichTextType.BOT_COMMAND)]
            | Annotated[RichTextButton, Tag(RichTextType.BUTTON)]
            | Annotated[RichTextAnchor, Tag(RichTextType.ANCHOR)]
            | Annotated[RichTextAnchorLink, Tag(RichTextType.ANCHOR_LINK)]
            | Annotated[RichTextReference, Tag(RichTextType.REFERENCE)]
            | Annotated[RichTextReferenceLink, Tag(RichTextType.REFERENCE_LINK)],
            Discriminator(_rich_text_union_tag),
        ],
    )
