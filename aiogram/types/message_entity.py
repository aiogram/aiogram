from __future__ import annotations

import warnings
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
    """Type of the entity. Can be 'mention' (:code:`@username`), 'hashtag' (:code:`#hashtag`), 'cashtag' (:code:`$USD`), 'bot_command' (:code:`/start@jobs_bot`), 'url' (:code:`https://telegram.org`), 'email' (:code:`do-not-reply@telegram.org`), 'phone_number' (:code:`+1-212-555-0123`), 'bold' (**bold text**), 'italic' (*italic text*), 'underline' (underlined text), 'strikethrough' (strikethrough text), 'code' (monowidth string), 'pre' (monowidth block), 'text_link' (for clickable text URLs), 'text_mention' (for users `without usernames <https://telegram.org/blog/edit#new-mentions>`_)"""
    offset: int
    """Offset in UTF-16 code units to the start of the entity"""
    length: int
    """Length of the entity in UTF-16 code units"""
    url: Optional[str] = None
    """*Optional*. For 'text_link' only, url that will be opened after user taps on the text"""
    user: Optional[User] = None
    """*Optional*. For 'text_mention' only, the mentioned user"""
    language: Optional[str] = None
    """*Optional*. For 'pre' only, the programming language of the entity text"""

    def extract(self, text: str) -> str:
        return remove_surrogates(
            add_surrogates(text)[self.offset * 2 : (self.offset + self.length) * 2]
        )

    def get_text(self, text: str) -> str:
        warnings.warn(
            "Method `MessageEntity.get_text(...)` deprecated and will be removed in 3.2.\n"
            " Use `MessageEntity.extract(...)` instead.",
            DeprecationWarning,
        )
        return self.extract(text=text)
