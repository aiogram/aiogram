from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject
from ...utils import helper

if TYPE_CHECKING:  # pragma: no cover
    from .chat_permissions import ChatPermissions
    from .chat_photo import ChatPhoto
    from .message import Message


class Chat(TelegramObject):
    """
    This object represents a chat.

    Source: https://core.telegram.org/bots/api#chat
    """

    id: int
    """Unique identifier for this chat. This number may be greater than 32 bits and some
    programming languages may have difficulty/silent defects in interpreting it. But it is
    smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe
    for storing this identifier."""
    type: str
    """Type of chat, can be either 'private', 'group', 'supergroup' or 'channel'"""
    title: Optional[str] = None
    """Title, for supergroups, channels and group chats"""
    username: Optional[str] = None
    """Username, for private chats, supergroups and channels if available"""
    first_name: Optional[str] = None
    """First name of the other party in a private chat"""
    last_name: Optional[str] = None
    """Last name of the other party in a private chat"""
    photo: Optional[ChatPhoto] = None
    """Chat photo. Returned only in getChat."""
    description: Optional[str] = None
    """Description, for groups, supergroups and channel chats. Returned only in getChat."""
    invite_link: Optional[str] = None
    """Chat invite link, for groups, supergroups and channel chats. Each administrator in a chat
    generates their own invite links, so the bot must first generate the link using
    exportChatInviteLink. Returned only in getChat."""
    pinned_message: Optional[Message] = None
    """Pinned message, for groups, supergroups and channels. Returned only in getChat."""
    permissions: Optional[ChatPermissions] = None
    """Default chat member permissions, for groups and supergroups. Returned only in getChat."""
    slow_mode_delay: Optional[int] = None
    """For supergroups, the minimum allowed delay between consecutive messages sent by each
    unpriviledged user. Returned only in getChat."""
    sticker_set_name: Optional[str] = None
    """For supergroups, name of group sticker set. Returned only in getChat."""
    can_set_sticker_set: Optional[bool] = None
    """True, if the bot can change the group sticker set. Returned only in getChat."""

    @property
    def full_name(self) -> str:
        """
        Get user's full name for private chats and chat title for groups/channels.
        """
        if self.type == ChatType.PRIVATE:
            return f'{self.first_name} {self.last_name}' if self.last_name else self.first_name

        return self.title

    @property
    def mention(self) -> Optional[str]:
        """
        Get mention if a Chat has a username, or get full name if this is a Private Chat, otherwise None is returned.
        """
        if self.username:
            return f'@{self.username}'
        elif self.type == ChatType.PRIVATE:
            return self.full_name

        return None

    @property
    def user_url(self) -> str:
        """
        Get user's url (only for private chats!). URL works only if user doesn't have forward privacy enabled.
        """
        if self.type != ChatType.PRIVATE:
            raise TypeError('\"user_url\" property is only available in private chats!')

        return f"tg://user?id={self.id}"


class ChatType(helper.Helper):
    """
    List of chat types
    :key: PRIVATE
    :key: GROUP
    :key: SUPER_GROUP
    :key: CHANNEL
    """

    mode = helper.HelperMode.lowercase

    PRIVATE = helper.Item()  # private
    GROUP = helper.Item()  # group
    SUPER_GROUP = helper.Item()  # supergroup
    CHANNEL = helper.Item()  # channel
