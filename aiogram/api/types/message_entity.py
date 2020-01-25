from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .user import User


class MessageEntity(TelegramObject):
    """
    This object represents one special entity in a text message. For example, hashtags, usernames,
    URLs, etc.

    Source: https://core.telegram.org/bots/api#messageentity
    """

    type: str
    """Type of the entity. Can be 'mention' (@username), 'hashtag' (#hashtag), 'cashtag' ($USD),
    'bot_command' (/start@jobs_bot), 'url' (https://telegram.org), 'email'
    (do-not-reply@telegram.org), 'phone_number' (+1-212-555-0123), 'bold' (bold text), 'italic'
    (italic text), 'underline' (underlined text), 'strikethrough' (strikethrough text), 'code'
    (monowidth string), 'pre' (monowidth block), 'text_link' (for clickable text URLs),
    'text_mention' (for users without usernames)"""
    offset: int
    """Offset in UTF-16 code units to the start of the entity"""
    length: int
    """Length of the entity in UTF-16 code units"""
    url: Optional[str] = None
    """For 'text_link' only, url that will be opened after user taps on the text"""
    user: Optional[User] = None
    """For 'text_mention' only, the mentioned user"""
    language: Optional[str] = None
    """For 'pre' only, the programming language of the entity text"""
