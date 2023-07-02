from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..utils.text_decorations import add_surrogates, remove_surrogates
from .base import MutableTelegramObject

if TYPE_CHECKING:
    from .user import User


class MessageEntity(MutableTelegramObject):
    """
    This object represents one special entity in a text message. For example, hashtags, usernames, URLs, etc.

    Source: https://core.telegram.org/bots/api#messageentity
    """

    type: str
    """Type of the entity. Currently, can be 'mention' (:code:`@username`), 'hashtag' (:code:`#hashtag`), 'cashtag' (:code:`$USD`), 'bot_command' (:code:`/start@jobs_bot`), 'url' (:code:`https://telegram.org`), 'email' (:code:`do-not-reply@telegram.org`), 'phone_number' (:code:`+1-212-555-0123`), 'bold' (**bold text**), 'italic' (*italic text*), 'underline' (underlined text), 'strikethrough' (strikethrough text), 'spoiler' (spoiler message), 'code' (monowidth string), 'pre' (monowidth block), 'text_link' (for clickable text URLs), 'text_mention' (for users `without usernames <https://telegram.org/blog/edit#new-mentions>`_), 'custom_emoji' (for inline custom emoji stickers)"""
    offset: int
    """Offset in `UTF-16 code units <https://core.telegram.org/api/entities#entity-length>`_ to the start of the entity"""
    length: int
    """Length of the entity in `UTF-16 code units <https://core.telegram.org/api/entities#entity-length>`_"""
    url: Optional[str] = None
    """*Optional*. For 'text_link' only, URL that will be opened after user taps on the text"""
    user: Optional[User] = None
    """*Optional*. For 'text_mention' only, the mentioned user"""
    language: Optional[str] = None
    """*Optional*. For 'pre' only, the programming language of the entity text"""
    custom_emoji_id: Optional[str] = None
    """*Optional*. For 'custom_emoji' only, unique identifier of the custom emoji. Use :class:`aiogram.methods.get_custom_emoji_stickers.GetCustomEmojiStickers` to get full information about the sticker"""

    def extract_from(self, text: str) -> str:
        return remove_surrogates(
            add_surrogates(text)[self.offset * 2 : (self.offset + self.length) * 2]
        )
