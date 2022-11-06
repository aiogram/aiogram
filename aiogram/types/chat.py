from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import BanChatSenderChat, UnbanChatSenderChat
    from .chat_location import ChatLocation
    from .chat_permissions import ChatPermissions
    from .chat_photo import ChatPhoto
    from .message import Message


class Chat(TelegramObject):
    """
    This object represents a chat.

    Source: https://core.telegram.org/bots/api#chat
    """

    id: int
    """Unique identifier for this chat. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this identifier."""
    type: str
    """Type of chat, can be either 'private', 'group', 'supergroup' or 'channel'"""
    title: Optional[str] = None
    """*Optional*. Title, for supergroups, channels and group chats"""
    username: Optional[str] = None
    """*Optional*. Username, for private chats, supergroups and channels if available"""
    first_name: Optional[str] = None
    """*Optional*. First name of the other party in a private chat"""
    last_name: Optional[str] = None
    """*Optional*. Last name of the other party in a private chat"""
    is_forum: Optional[bool] = None
    """*Optional*. :code:`True`, if the supergroup chat is a forum (has `topics <https://telegram.org/blog/topics-in-groups-collectible-usernames#topics-in-groups>`_ enabled)"""
    photo: Optional[ChatPhoto] = None
    """*Optional*. Chat photo. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    active_usernames: Optional[List[str]] = None
    """*Optional*. If non-empty, the list of all `active chat usernames <https://telegram.org/blog/topics-in-groups-collectible-usernames#collectible-usernames>`_; for private chats, supergroups and channels. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    emoji_status_custom_emoji_id: Optional[str] = None
    """*Optional*. Custom emoji identifier of emoji status of the other party in a private chat. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    bio: Optional[str] = None
    """*Optional*. Bio of the other party in a private chat. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    has_private_forwards: Optional[bool] = None
    """*Optional*. :code:`True`, if privacy settings of the other party in the private chat allows to use :code:`tg://user?id=<user_id>` links only in chats with the user. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    has_restricted_voice_and_video_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the privacy settings of the other party restrict sending voice and video note messages in the private chat. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    join_to_send_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if users need to join the supergroup before they can send messages. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    join_by_request: Optional[bool] = None
    """*Optional*. :code:`True`, if all users directly joining the supergroup need to be approved by supergroup administrators. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    description: Optional[str] = None
    """*Optional*. Description, for groups, supergroups and channel chats. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    invite_link: Optional[str] = None
    """*Optional*. Primary invite link, for groups, supergroups and channel chats. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    pinned_message: Optional[Message] = None
    """*Optional*. The most recent pinned message (by sending date). Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    permissions: Optional[ChatPermissions] = None
    """*Optional*. Default chat member permissions, for groups and supergroups. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    slow_mode_delay: Optional[int] = None
    """*Optional*. For supergroups, the minimum allowed delay between consecutive messages sent by each unpriviledged user; in seconds. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    message_auto_delete_time: Optional[int] = None
    """*Optional*. The time after which all messages sent to the chat will be automatically deleted; in seconds. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    has_protected_content: Optional[bool] = None
    """*Optional*. :code:`True`, if messages from the chat can't be forwarded to other chats. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    sticker_set_name: Optional[str] = None
    """*Optional*. For supergroups, name of group sticker set. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    can_set_sticker_set: Optional[bool] = None
    """*Optional*. :code:`True`, if the bot can change the group sticker set. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    linked_chat_id: Optional[int] = None
    """*Optional*. Unique identifier for the linked chat, i.e. the discussion group identifier for a channel and vice versa; for supergroups and channel chats. This identifier may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    location: Optional[ChatLocation] = None
    """*Optional*. For supergroups, the location to which the supergroup is connected. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""

    @property
    def shifted_id(self) -> int:
        """
        Returns shifted chat ID (positive and without "-100" prefix).
        Mostly used for private links like t.me/c/chat_id/message_id

        Currently supergroup/channel IDs have 10-digit ID after "-100" prefix removed.
        However, these IDs might become 11-digit in future. So, first we remove "-100"
        prefix and count remaining number length. Then we multiple
        -1 * 10 ^ (number_length + 2)
        Finally, self.id is substracted from that number
        """
        short_id = str(self.id).replace("-100", "")
        shift = int(-1 * pow(10, len(short_id) + 2))
        return shift - self.id

    @property
    def full_name(self) -> str:
        """Get full name of the Chat.

        For private chat it is first_name + last_name.
        For other chat types it is title.
        """
        if self.title is not None:
            return self.title

        if self.last_name is not None:
            return f"{self.first_name} {self.last_name}"

        return f"{self.first_name}"

    def ban_sender_chat(self, sender_chat_id: int) -> BanChatSenderChat:
        from ..methods import BanChatSenderChat

        return BanChatSenderChat(
            chat_id=self.id,
            sender_chat_id=sender_chat_id,
        )

    def unban_sender_chat(self, sender_chat_id: int) -> UnbanChatSenderChat:
        from ..methods import UnbanChatSenderChat

        return UnbanChatSenderChat(
            chat_id=self.id,
            sender_chat_id=sender_chat_id,
        )
