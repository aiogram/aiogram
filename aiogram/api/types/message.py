from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import Field

from .base import TelegramObject

if TYPE_CHECKING:
    from .voice import Voice
    from .contact import Contact
    from .game import Game
    from .venue import Venue
    from .document import Document
    from .audio import Audio
    from .invoice import Invoice
    from .location import Location
    from .photo_size import PhotoSize
    from .chat import Chat
    from .sticker import Sticker
    from .animation import Animation
    from .poll import Poll
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .user import User
    from .message_entity import MessageEntity
    from .successful_payment import SuccessfulPayment
    from .passport_data import PassportData
    from .video import Video
    from .video_note import VideoNote


class Message(TelegramObject):
    """
    This object represents a message.

    Source: https://core.telegram.org/bots/api#message
    """

    message_id: int
    """Unique message identifier inside this chat"""
    date: datetime.datetime
    """Date the message was sent in Unix time"""
    chat: Chat
    """Conversation the message belongs to"""
    from_user: Optional[User] = Field(None, alias="from")
    """Sender, empty for messages sent to channels"""
    forward_from: Optional[User] = None
    """For forwarded messages, sender of the original message"""
    forward_from_chat: Optional[Chat] = None
    """For messages forwarded from channels, information about the original channel"""
    forward_from_message_id: Optional[int] = None
    """For messages forwarded from channels, identifier of the original message in the channel"""
    forward_signature: Optional[str] = None
    """For messages forwarded from channels, signature of the post author if present"""
    forward_sender_name: Optional[str] = None
    """Sender's name for messages forwarded from users who disallow adding a link to their account in forwarded messages"""
    forward_date: Optional[int] = None
    """For forwarded messages, date the original message was sent in Unix time"""
    reply_to_message: Optional[Message] = None
    """For replies, the original message. Note that the Message object in this field will not contain further reply_to_message fields even if it itself is a reply."""
    edit_date: Optional[int] = None
    """Date the message was last edited in Unix time"""
    media_group_id: Optional[str] = None
    """The unique identifier of a media message group this message belongs to"""
    author_signature: Optional[str] = None
    """Signature of the post author for messages in channels"""
    text: Optional[str] = None
    """For text messages, the actual UTF-8 text of the message, 0-4096 characters."""
    entities: Optional[List[MessageEntity]] = None
    """For text messages, special entities like usernames, URLs, bot commands, etc. that appear in the text"""
    caption_entities: Optional[List[MessageEntity]] = None
    """For messages with a caption, special entities like usernames, URLs, bot commands, etc. that appear in the caption"""
    audio: Optional[Audio] = None
    """Message is an audio file, information about the file"""
    document: Optional[Document] = None
    """Message is a general file, information about the file"""
    animation: Optional[Animation] = None
    """Message is an animation, information about the animation. For backward compatibility, when this field is set, the document field will also be set"""
    game: Optional[Game] = None
    """Message is a game, information about the game."""
    photo: Optional[List[PhotoSize]] = None
    """Message is a photo, available sizes of the photo"""
    sticker: Optional[Sticker] = None
    """Message is a sticker, information about the sticker"""
    video: Optional[Video] = None
    """Message is a video, information about the video"""
    voice: Optional[Voice] = None
    """Message is a voice message, information about the file"""
    video_note: Optional[VideoNote] = None
    """Message is a video note, information about the video message"""
    caption: Optional[str] = None
    """Caption for the animation, audio, document, photo, video or voice, 0-1024 characters"""
    contact: Optional[Contact] = None
    """Message is a shared contact, information about the contact"""
    location: Optional[Location] = None
    """Message is a shared location, information about the location"""
    venue: Optional[Venue] = None
    """Message is a venue, information about the venue"""
    poll: Optional[Poll] = None
    """Message is a native poll, information about the poll"""
    new_chat_members: Optional[List[User]] = None
    """New members that were added to the group or supergroup and information about them (the bot itself may be one of these members)"""
    left_chat_member: Optional[User] = None
    """A member was removed from the group, information about them (this member may be the bot itself)"""
    new_chat_title: Optional[str] = None
    """A chat title was changed to this value"""
    new_chat_photo: Optional[List[PhotoSize]] = None
    """A chat photo was change to this value"""
    delete_chat_photo: Optional[bool] = None
    """Service message: the chat photo was deleted"""
    group_chat_created: Optional[bool] = None
    """Service message: the group has been created"""
    supergroup_chat_created: Optional[bool] = None
    """Service message: the supergroup has been created. This field can‘t be received in a message coming through updates, because bot can’t be a member of a supergroup when it is created. It can only be found in reply_to_message if someone replies to a very first message in a directly created supergroup."""
    channel_chat_created: Optional[bool] = None
    """Service message: the channel has been created. This field can‘t be received in a message coming through updates, because bot can’t be a member of a channel when it is created. It can only be found in reply_to_message if someone replies to a very first message in a channel."""
    migrate_to_chat_id: Optional[int] = None
    """The group has been migrated to a supergroup with the specified identifier. This number may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier."""
    migrate_from_chat_id: Optional[int] = None
    """The supergroup has been migrated from a group with the specified identifier. This number may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier."""
    pinned_message: Optional[Message] = None
    """Specified message was pinned. Note that the Message object in this field will not contain further reply_to_message fields even if it is itself a reply."""
    invoice: Optional[Invoice] = None
    """Message is an invoice for a payment, information about the invoice."""
    successful_payment: Optional[SuccessfulPayment] = None
    """Message is a service message about a successful payment, information about the payment."""
    connected_website: Optional[str] = None
    """The domain name of the website on which the user has logged in."""
    passport_data: Optional[PassportData] = None
    """Telegram Passport data"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message. login_url buttons are represented as ordinary url buttons."""
