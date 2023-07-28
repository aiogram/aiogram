from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, List, Optional, Union

from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import (
        BanChatMember,
        BanChatSenderChat,
        CreateChatInviteLink,
        DeleteChatPhoto,
        DeleteChatStickerSet,
        DeleteMessage,
        EditChatInviteLink,
        ExportChatInviteLink,
        GetChatAdministrators,
        GetChatMember,
        GetChatMemberCount,
        LeaveChat,
        PinChatMessage,
        PromoteChatMember,
        RestrictChatMember,
        RevokeChatInviteLink,
        SendChatAction,
        SetChatAdministratorCustomTitle,
        SetChatDescription,
        SetChatPermissions,
        SetChatPhoto,
        SetChatStickerSet,
        SetChatTitle,
        UnbanChatMember,
        UnbanChatSenderChat,
        UnpinAllChatMessages,
        UnpinChatMessage,
    )
    from .chat_location import ChatLocation
    from .chat_permissions import ChatPermissions
    from .chat_photo import ChatPhoto
    from .input_file import InputFile
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
    has_aggressive_anti_spam_enabled: Optional[bool] = None
    """*Optional*. :code:`True`, if aggressive anti-spam checks are enabled in the supergroup. The field is only available to chat administrators. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
    has_hidden_members: Optional[bool] = None
    """*Optional*. :code:`True`, if non-administrators can only get the list of bots and administrators in the chat. Returned only in :class:`aiogram.methods.get_chat.GetChat`."""
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

    def ban_sender_chat(
        self,
        sender_chat_id: int,
        **kwargs: Any,
    ) -> BanChatSenderChat:
        """
        Shortcut for method :class:`aiogram.methods.ban_chat_sender_chat.BanChatSenderChat`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to ban a channel chat in a supergroup or a channel. Until the chat is `unbanned <https://core.telegram.org/bots/api#unbanchatsenderchat>`_, the owner of the banned chat won't be able to send messages on behalf of **any of their channels**. The bot must be an administrator in the supergroup or channel for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#banchatsenderchat

        :param sender_chat_id: Unique identifier of the target sender chat
        :return: instance of method :class:`aiogram.methods.ban_chat_sender_chat.BanChatSenderChat`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import BanChatSenderChat

        return BanChatSenderChat(
            chat_id=self.id,
            sender_chat_id=sender_chat_id,
            **kwargs,
        ).as_(self._bot)

    def unban_sender_chat(
        self,
        sender_chat_id: int,
        **kwargs: Any,
    ) -> UnbanChatSenderChat:
        """
        Shortcut for method :class:`aiogram.methods.unban_chat_sender_chat.UnbanChatSenderChat`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to unban a previously banned channel chat in a supergroup or channel. The bot must be an administrator for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#unbanchatsenderchat

        :param sender_chat_id: Unique identifier of the target sender chat
        :return: instance of method :class:`aiogram.methods.unban_chat_sender_chat.UnbanChatSenderChat`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import UnbanChatSenderChat

        return UnbanChatSenderChat(
            chat_id=self.id,
            sender_chat_id=sender_chat_id,
            **kwargs,
        ).as_(self._bot)

    def get_administrators(
        self,
        **kwargs: Any,
    ) -> GetChatAdministrators:
        """
        Shortcut for method :class:`aiogram.methods.get_chat_administrators.GetChatAdministrators`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to get a list of administrators in a chat, which aren't bots. Returns an Array of :class:`aiogram.types.chat_member.ChatMember` objects.

        Source: https://core.telegram.org/bots/api#getchatadministrators

        :return: instance of method :class:`aiogram.methods.get_chat_administrators.GetChatAdministrators`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import GetChatAdministrators

        return GetChatAdministrators(
            chat_id=self.id,
            **kwargs,
        ).as_(self._bot)

    def delete_message(
        self,
        message_id: int,
        **kwargs: Any,
    ) -> DeleteMessage:
        """
        Shortcut for method :class:`aiogram.methods.delete_message.DeleteMessage`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to delete a message, including service messages, with the following limitations:

        - A message can only be deleted if it was sent less than 48 hours ago.

        - Service messages about a supergroup, channel, or forum topic creation can't be deleted.

        - A dice message in a private chat can only be deleted if it was sent more than 24 hours ago.

        - Bots can delete outgoing messages in private chats, groups, and supergroups.

        - Bots can delete incoming messages in private chats.

        - Bots granted *can_post_messages* permissions can delete outgoing messages in channels.

        - If the bot is an administrator of a group, it can delete any message there.

        - If the bot has *can_delete_messages* permission in a supergroup or a channel, it can delete any message there.

        Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#deletemessage

        :param message_id: Identifier of the message to delete
        :return: instance of method :class:`aiogram.methods.delete_message.DeleteMessage`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import DeleteMessage

        return DeleteMessage(
            chat_id=self.id,
            message_id=message_id,
            **kwargs,
        ).as_(self._bot)

    def revoke_invite_link(
        self,
        invite_link: str,
        **kwargs: Any,
    ) -> RevokeChatInviteLink:
        """
        Shortcut for method :class:`aiogram.methods.revoke_chat_invite_link.RevokeChatInviteLink`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to revoke an invite link created by the bot. If the primary link is revoked, a new link is automatically generated. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the revoked invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

        Source: https://core.telegram.org/bots/api#revokechatinvitelink

        :param invite_link: The invite link to revoke
        :return: instance of method :class:`aiogram.methods.revoke_chat_invite_link.RevokeChatInviteLink`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import RevokeChatInviteLink

        return RevokeChatInviteLink(
            chat_id=self.id,
            invite_link=invite_link,
            **kwargs,
        ).as_(self._bot)

    def edit_invite_link(
        self,
        invite_link: str,
        name: Optional[str] = None,
        expire_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        member_limit: Optional[int] = None,
        creates_join_request: Optional[bool] = None,
        **kwargs: Any,
    ) -> EditChatInviteLink:
        """
        Shortcut for method :class:`aiogram.methods.edit_chat_invite_link.EditChatInviteLink`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to edit a non-primary invite link created by the bot. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the edited invite link as a :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

        Source: https://core.telegram.org/bots/api#editchatinvitelink

        :param invite_link: The invite link to edit
        :param name: Invite link name; 0-32 characters
        :param expire_date: Point in time (Unix timestamp) when the link will expire
        :param member_limit: The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999
        :param creates_join_request: :code:`True`, if users joining the chat via the link need to be approved by chat administrators. If :code:`True`, *member_limit* can't be specified
        :return: instance of method :class:`aiogram.methods.edit_chat_invite_link.EditChatInviteLink`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditChatInviteLink

        return EditChatInviteLink(
            chat_id=self.id,
            invite_link=invite_link,
            name=name,
            expire_date=expire_date,
            member_limit=member_limit,
            creates_join_request=creates_join_request,
            **kwargs,
        ).as_(self._bot)

    def create_invite_link(
        self,
        name: Optional[str] = None,
        expire_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        member_limit: Optional[int] = None,
        creates_join_request: Optional[bool] = None,
        **kwargs: Any,
    ) -> CreateChatInviteLink:
        """
        Shortcut for method :class:`aiogram.methods.create_chat_invite_link.CreateChatInviteLink`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to create an additional invite link for a chat. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. The link can be revoked using the method :class:`aiogram.methods.revoke_chat_invite_link.RevokeChatInviteLink`. Returns the new invite link as :class:`aiogram.types.chat_invite_link.ChatInviteLink` object.

        Source: https://core.telegram.org/bots/api#createchatinvitelink

        :param name: Invite link name; 0-32 characters
        :param expire_date: Point in time (Unix timestamp) when the link will expire
        :param member_limit: The maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999
        :param creates_join_request: :code:`True`, if users joining the chat via the link need to be approved by chat administrators. If :code:`True`, *member_limit* can't be specified
        :return: instance of method :class:`aiogram.methods.create_chat_invite_link.CreateChatInviteLink`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import CreateChatInviteLink

        return CreateChatInviteLink(
            chat_id=self.id,
            name=name,
            expire_date=expire_date,
            member_limit=member_limit,
            creates_join_request=creates_join_request,
            **kwargs,
        ).as_(self._bot)

    def export_invite_link(
        self,
        **kwargs: Any,
    ) -> ExportChatInviteLink:
        """
        Shortcut for method :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to generate a new primary invite link for a chat; any previously generated primary link is revoked. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns the new invite link as *String* on success.

         Note: Each administrator in a chat generates their own invite links. Bots can't use invite links generated by other administrators. If you want your bot to work with invite links, it will need to generate its own link using :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink` or by calling the :class:`aiogram.methods.get_chat.GetChat` method. If your bot needs to generate a new primary invite link replacing its previous one, use :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink` again.

        Source: https://core.telegram.org/bots/api#exportchatinvitelink

        :return: instance of method :class:`aiogram.methods.export_chat_invite_link.ExportChatInviteLink`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import ExportChatInviteLink

        return ExportChatInviteLink(
            chat_id=self.id,
            **kwargs,
        ).as_(self._bot)

    def do(
        self,
        action: str,
        message_thread_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendChatAction:
        """
        Shortcut for method :class:`aiogram.methods.send_chat_action.SendChatAction`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method when you need to tell the user that something is happening on the bot's side. The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status). Returns :code:`True` on success.

         Example: The `ImageBot <https://t.me/imagebot>`_ needs some time to process a request and upload the image. Instead of sending a text message along the lines of 'Retrieving image, please wait…', the bot may use :class:`aiogram.methods.send_chat_action.SendChatAction` with *action* = *upload_photo*. The user will see a 'sending photo' status for the bot.

        We only recommend using this method when a response from the bot will take a **noticeable** amount of time to arrive.

        Source: https://core.telegram.org/bots/api#sendchataction

        :param action: Type of action to broadcast. Choose one, depending on what the user is about to receive: *typing* for `text messages <https://core.telegram.org/bots/api#sendmessage>`_, *upload_photo* for `photos <https://core.telegram.org/bots/api#sendphoto>`_, *record_video* or *upload_video* for `videos <https://core.telegram.org/bots/api#sendvideo>`_, *record_voice* or *upload_voice* for `voice notes <https://core.telegram.org/bots/api#sendvoice>`_, *upload_document* for `general files <https://core.telegram.org/bots/api#senddocument>`_, *choose_sticker* for `stickers <https://core.telegram.org/bots/api#sendsticker>`_, *find_location* for `location data <https://core.telegram.org/bots/api#sendlocation>`_, *record_video_note* or *upload_video_note* for `video notes <https://core.telegram.org/bots/api#sendvideonote>`_.
        :param message_thread_id: Unique identifier for the target message thread; supergroups only
        :return: instance of method :class:`aiogram.methods.send_chat_action.SendChatAction`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendChatAction

        return SendChatAction(
            chat_id=self.id,
            action=action,
            message_thread_id=message_thread_id,
            **kwargs,
        ).as_(self._bot)

    def delete_sticker_set(
        self,
        **kwargs: Any,
    ) -> DeleteChatStickerSet:
        """
        Shortcut for method :class:`aiogram.methods.delete_chat_sticker_set.DeleteChatStickerSet`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field *can_set_sticker_set* optionally returned in :class:`aiogram.methods.get_chat.GetChat` requests to check if the bot can use this method. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#deletechatstickerset

        :return: instance of method :class:`aiogram.methods.delete_chat_sticker_set.DeleteChatStickerSet`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import DeleteChatStickerSet

        return DeleteChatStickerSet(
            chat_id=self.id,
            **kwargs,
        ).as_(self._bot)

    def set_sticker_set(
        self,
        sticker_set_name: str,
        **kwargs: Any,
    ) -> SetChatStickerSet:
        """
        Shortcut for method :class:`aiogram.methods.set_chat_sticker_set.SetChatStickerSet`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Use the field *can_set_sticker_set* optionally returned in :class:`aiogram.methods.get_chat.GetChat` requests to check if the bot can use this method. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchatstickerset

        :param sticker_set_name: Name of the sticker set to be set as the group sticker set
        :return: instance of method :class:`aiogram.methods.set_chat_sticker_set.SetChatStickerSet`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SetChatStickerSet

        return SetChatStickerSet(
            chat_id=self.id,
            sticker_set_name=sticker_set_name,
            **kwargs,
        ).as_(self._bot)

    def get_member(
        self,
        user_id: int,
        **kwargs: Any,
    ) -> GetChatMember:
        """
        Shortcut for method :class:`aiogram.methods.get_chat_member.GetChatMember`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to get information about a member of a chat. The method is only guaranteed to work for other users if the bot is an administrator in the chat. Returns a :class:`aiogram.types.chat_member.ChatMember` object on success.

        Source: https://core.telegram.org/bots/api#getchatmember

        :param user_id: Unique identifier of the target user
        :return: instance of method :class:`aiogram.methods.get_chat_member.GetChatMember`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import GetChatMember

        return GetChatMember(
            chat_id=self.id,
            user_id=user_id,
            **kwargs,
        ).as_(self._bot)

    def get_member_count(
        self,
        **kwargs: Any,
    ) -> GetChatMemberCount:
        """
        Shortcut for method :class:`aiogram.methods.get_chat_member_count.GetChatMemberCount`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to get the number of members in a chat. Returns *Int* on success.

        Source: https://core.telegram.org/bots/api#getchatmembercount

        :return: instance of method :class:`aiogram.methods.get_chat_member_count.GetChatMemberCount`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import GetChatMemberCount

        return GetChatMemberCount(
            chat_id=self.id,
            **kwargs,
        ).as_(self._bot)

    def leave(
        self,
        **kwargs: Any,
    ) -> LeaveChat:
        """
        Shortcut for method :class:`aiogram.methods.leave_chat.LeaveChat`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method for your bot to leave a group, supergroup or channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#leavechat

        :return: instance of method :class:`aiogram.methods.leave_chat.LeaveChat`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import LeaveChat

        return LeaveChat(
            chat_id=self.id,
            **kwargs,
        ).as_(self._bot)

    def unpin_all_messages(
        self,
        **kwargs: Any,
    ) -> UnpinAllChatMessages:
        """
        Shortcut for method :class:`aiogram.methods.unpin_all_chat_messages.UnpinAllChatMessages`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to clear the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#unpinallchatmessages

        :return: instance of method :class:`aiogram.methods.unpin_all_chat_messages.UnpinAllChatMessages`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import UnpinAllChatMessages

        return UnpinAllChatMessages(
            chat_id=self.id,
            **kwargs,
        ).as_(self._bot)

    def unpin_message(
        self,
        message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> UnpinChatMessage:
        """
        Shortcut for method :class:`aiogram.methods.unpin_chat_message.UnpinChatMessage`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#unpinchatmessage

        :param message_id: Identifier of a message to unpin. If not specified, the most recent pinned message (by sending date) will be unpinned.
        :return: instance of method :class:`aiogram.methods.unpin_chat_message.UnpinChatMessage`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import UnpinChatMessage

        return UnpinChatMessage(
            chat_id=self.id,
            message_id=message_id,
            **kwargs,
        ).as_(self._bot)

    def pin_message(
        self,
        message_id: int,
        disable_notification: Optional[bool] = None,
        **kwargs: Any,
    ) -> PinChatMessage:
        """
        Shortcut for method :class:`aiogram.methods.pin_chat_message.PinChatMessage`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to add a message to the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#pinchatmessage

        :param message_id: Identifier of a message to pin
        :param disable_notification: Pass :code:`True` if it is not necessary to send a notification to all chat members about the new pinned message. Notifications are always disabled in channels and private chats.
        :return: instance of method :class:`aiogram.methods.pin_chat_message.PinChatMessage`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import PinChatMessage

        return PinChatMessage(
            chat_id=self.id,
            message_id=message_id,
            disable_notification=disable_notification,
            **kwargs,
        ).as_(self._bot)

    def set_administrator_custom_title(
        self,
        user_id: int,
        custom_title: str,
        **kwargs: Any,
    ) -> SetChatAdministratorCustomTitle:
        """
        Shortcut for method :class:`aiogram.methods.set_chat_administrator_custom_title.SetChatAdministratorCustomTitle`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to set a custom title for an administrator in a supergroup promoted by the bot. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchatadministratorcustomtitle

        :param user_id: Unique identifier of the target user
        :param custom_title: New custom title for the administrator; 0-16 characters, emoji are not allowed
        :return: instance of method :class:`aiogram.methods.set_chat_administrator_custom_title.SetChatAdministratorCustomTitle`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SetChatAdministratorCustomTitle

        return SetChatAdministratorCustomTitle(
            chat_id=self.id,
            user_id=user_id,
            custom_title=custom_title,
            **kwargs,
        ).as_(self._bot)

    def set_permissions(
        self,
        permissions: ChatPermissions,
        use_independent_chat_permissions: Optional[bool] = None,
        **kwargs: Any,
    ) -> SetChatPermissions:
        """
        Shortcut for method :class:`aiogram.methods.set_chat_permissions.SetChatPermissions`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the *can_restrict_members* administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchatpermissions

        :param permissions: A JSON-serialized object for new default chat permissions
        :param use_independent_chat_permissions: Pass :code:`True` if chat permissions are set independently. Otherwise, the *can_send_other_messages* and *can_add_web_page_previews* permissions will imply the *can_send_messages*, *can_send_audios*, *can_send_documents*, *can_send_photos*, *can_send_videos*, *can_send_video_notes*, and *can_send_voice_notes* permissions; the *can_send_polls* permission will imply the *can_send_messages* permission.
        :return: instance of method :class:`aiogram.methods.set_chat_permissions.SetChatPermissions`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SetChatPermissions

        return SetChatPermissions(
            chat_id=self.id,
            permissions=permissions,
            use_independent_chat_permissions=use_independent_chat_permissions,
            **kwargs,
        ).as_(self._bot)

    def promote(
        self,
        user_id: int,
        is_anonymous: Optional[bool] = None,
        can_manage_chat: Optional[bool] = None,
        can_post_messages: Optional[bool] = None,
        can_edit_messages: Optional[bool] = None,
        can_delete_messages: Optional[bool] = None,
        can_manage_video_chats: Optional[bool] = None,
        can_restrict_members: Optional[bool] = None,
        can_promote_members: Optional[bool] = None,
        can_change_info: Optional[bool] = None,
        can_invite_users: Optional[bool] = None,
        can_pin_messages: Optional[bool] = None,
        can_manage_topics: Optional[bool] = None,
        **kwargs: Any,
    ) -> PromoteChatMember:
        """
        Shortcut for method :class:`aiogram.methods.promote_chat_member.PromoteChatMember`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Pass :code:`False` for all boolean parameters to demote a user. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#promotechatmember

        :param user_id: Unique identifier of the target user
        :param is_anonymous: Pass :code:`True` if the administrator's presence in the chat is hidden
        :param can_manage_chat: Pass :code:`True` if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege
        :param can_post_messages: Pass :code:`True` if the administrator can create channel posts, channels only
        :param can_edit_messages: Pass :code:`True` if the administrator can edit messages of other users and can pin messages, channels only
        :param can_delete_messages: Pass :code:`True` if the administrator can delete messages of other users
        :param can_manage_video_chats: Pass :code:`True` if the administrator can manage video chats
        :param can_restrict_members: Pass :code:`True` if the administrator can restrict, ban or unban chat members
        :param can_promote_members: Pass :code:`True` if the administrator can add new administrators with a subset of their own privileges or demote administrators that they have promoted, directly or indirectly (promoted by administrators that were appointed by him)
        :param can_change_info: Pass :code:`True` if the administrator can change chat title, photo and other settings
        :param can_invite_users: Pass :code:`True` if the administrator can invite new users to the chat
        :param can_pin_messages: Pass :code:`True` if the administrator can pin messages, supergroups only
        :param can_manage_topics: Pass :code:`True` if the user is allowed to create, rename, close, and reopen forum topics, supergroups only
        :return: instance of method :class:`aiogram.methods.promote_chat_member.PromoteChatMember`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import PromoteChatMember

        return PromoteChatMember(
            chat_id=self.id,
            user_id=user_id,
            is_anonymous=is_anonymous,
            can_manage_chat=can_manage_chat,
            can_post_messages=can_post_messages,
            can_edit_messages=can_edit_messages,
            can_delete_messages=can_delete_messages,
            can_manage_video_chats=can_manage_video_chats,
            can_restrict_members=can_restrict_members,
            can_promote_members=can_promote_members,
            can_change_info=can_change_info,
            can_invite_users=can_invite_users,
            can_pin_messages=can_pin_messages,
            can_manage_topics=can_manage_topics,
            **kwargs,
        ).as_(self._bot)

    def restrict(
        self,
        user_id: int,
        permissions: ChatPermissions,
        use_independent_chat_permissions: Optional[bool] = None,
        until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        **kwargs: Any,
    ) -> RestrictChatMember:
        """
        Shortcut for method :class:`aiogram.methods.restrict_chat_member.RestrictChatMember`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate administrator rights. Pass :code:`True` for all permissions to lift restrictions from a user. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#restrictchatmember

        :param user_id: Unique identifier of the target user
        :param permissions: A JSON-serialized object for new user permissions
        :param use_independent_chat_permissions: Pass :code:`True` if chat permissions are set independently. Otherwise, the *can_send_other_messages* and *can_add_web_page_previews* permissions will imply the *can_send_messages*, *can_send_audios*, *can_send_documents*, *can_send_photos*, *can_send_videos*, *can_send_video_notes*, and *can_send_voice_notes* permissions; the *can_send_polls* permission will imply the *can_send_messages* permission.
        :param until_date: Date when restrictions will be lifted for the user, unix time. If user is restricted for more than 366 days or less than 30 seconds from the current time, they are considered to be restricted forever
        :return: instance of method :class:`aiogram.methods.restrict_chat_member.RestrictChatMember`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import RestrictChatMember

        return RestrictChatMember(
            chat_id=self.id,
            user_id=user_id,
            permissions=permissions,
            use_independent_chat_permissions=use_independent_chat_permissions,
            until_date=until_date,
            **kwargs,
        ).as_(self._bot)

    def unban(
        self,
        user_id: int,
        only_if_banned: Optional[bool] = None,
        **kwargs: Any,
    ) -> UnbanChatMember:
        """
        Shortcut for method :class:`aiogram.methods.unban_chat_member.UnbanChatMember`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to unban a previously banned user in a supergroup or channel. The user will **not** return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. By default, this method guarantees that after the call the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat they will also be **removed** from the chat. If you don't want this, use the parameter *only_if_banned*. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#unbanchatmember

        :param user_id: Unique identifier of the target user
        :param only_if_banned: Do nothing if the user is not banned
        :return: instance of method :class:`aiogram.methods.unban_chat_member.UnbanChatMember`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import UnbanChatMember

        return UnbanChatMember(
            chat_id=self.id,
            user_id=user_id,
            only_if_banned=only_if_banned,
            **kwargs,
        ).as_(self._bot)

    def ban(
        self,
        user_id: int,
        until_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        revoke_messages: Optional[bool] = None,
        **kwargs: Any,
    ) -> BanChatMember:
        """
        Shortcut for method :class:`aiogram.methods.ban_chat_member.BanChatMember`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to ban a user in a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc., unless `unbanned <https://core.telegram.org/bots/api#unbanchatmember>`_ first. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#banchatmember

        :param user_id: Unique identifier of the target user
        :param until_date: Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever. Applied for supergroups and channels only.
        :param revoke_messages: Pass :code:`True` to delete all messages from the chat for the user that is being removed. If :code:`False`, the user will be able to see messages in the group that were sent before the user was removed. Always :code:`True` for supergroups and channels.
        :return: instance of method :class:`aiogram.methods.ban_chat_member.BanChatMember`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import BanChatMember

        return BanChatMember(
            chat_id=self.id,
            user_id=user_id,
            until_date=until_date,
            revoke_messages=revoke_messages,
            **kwargs,
        ).as_(self._bot)

    def set_description(
        self,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> SetChatDescription:
        """
        Shortcut for method :class:`aiogram.methods.set_chat_description.SetChatDescription`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchatdescription

        :param description: New chat description, 0-255 characters
        :return: instance of method :class:`aiogram.methods.set_chat_description.SetChatDescription`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SetChatDescription

        return SetChatDescription(
            chat_id=self.id,
            description=description,
            **kwargs,
        ).as_(self._bot)

    def set_title(
        self,
        title: str,
        **kwargs: Any,
    ) -> SetChatTitle:
        """
        Shortcut for method :class:`aiogram.methods.set_chat_title.SetChatTitle`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchattitle

        :param title: New chat title, 1-128 characters
        :return: instance of method :class:`aiogram.methods.set_chat_title.SetChatTitle`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SetChatTitle

        return SetChatTitle(
            chat_id=self.id,
            title=title,
            **kwargs,
        ).as_(self._bot)

    def delete_photo(
        self,
        **kwargs: Any,
    ) -> DeleteChatPhoto:
        """
        Shortcut for method :class:`aiogram.methods.delete_chat_photo.DeleteChatPhoto`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#deletechatphoto

        :return: instance of method :class:`aiogram.methods.delete_chat_photo.DeleteChatPhoto`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import DeleteChatPhoto

        return DeleteChatPhoto(
            chat_id=self.id,
            **kwargs,
        ).as_(self._bot)

    def set_photo(
        self,
        photo: InputFile,
        **kwargs: Any,
    ) -> SetChatPhoto:
        """
        Shortcut for method :class:`aiogram.methods.set_chat_photo.SetChatPhoto`
        will automatically fill method attributes:

        - :code:`chat_id`

        Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate administrator rights. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setchatphoto

        :param photo: New chat photo, uploaded using multipart/form-data
        :return: instance of method :class:`aiogram.methods.set_chat_photo.SetChatPhoto`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SetChatPhoto

        return SetChatPhoto(
            chat_id=self.id,
            photo=photo,
            **kwargs,
        ).as_(self._bot)
