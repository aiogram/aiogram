from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from .chat import Chat
from .custom import DateTime

if TYPE_CHECKING:
    from .birthdate import Birthdate
    from .business_intro import BusinessIntro
    from .business_location import BusinessLocation
    from .business_opening_hours import BusinessOpeningHours
    from .chat_location import ChatLocation
    from .chat_permissions import ChatPermissions
    from .chat_photo import ChatPhoto
    from .message import Message
    from .reaction_type_custom_emoji import ReactionTypeCustomEmoji
    from .reaction_type_emoji import ReactionTypeEmoji
    from .reaction_type_paid import ReactionTypePaid


class ChatFullInfo(Chat):
    """
    This object contains full information about a chat.

    Source: https://core.telegram.org/bots/api#chatfullinfo
    """

    id: int
    """Unique identifier for this chat. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this identifier."""
    type: str
    """Type of the chat, can be either 'private', 'group', 'supergroup' or 'channel'"""
    accent_color_id: int
    """Identifier of the accent color for the chat name and backgrounds of the chat photo, reply header, and link preview. See `accent colors <https://core.telegram.org/bots/api#accent-colors>`_ for more details."""
    max_reaction_count: int
    """The maximum number of reactions that can be set on a message in the chat"""
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
    """*Optional*. Chat photo"""
    active_usernames: Optional[list[str]] = None
    """*Optional*. If non-empty, the list of all `active chat usernames <https://telegram.org/blog/topics-in-groups-collectible-usernames#collectible-usernames>`_; for private chats, supergroups and channels"""
    birthdate: Optional[Birthdate] = None
    """*Optional*. For private chats, the date of birth of the user"""
    business_intro: Optional[BusinessIntro] = None
    """*Optional*. For private chats with business accounts, the intro of the business"""
    business_location: Optional[BusinessLocation] = None
    """*Optional*. For private chats with business accounts, the location of the business"""
    business_opening_hours: Optional[BusinessOpeningHours] = None
    """*Optional*. For private chats with business accounts, the opening hours of the business"""
    personal_chat: Optional[Chat] = None
    """*Optional*. For private chats, the personal channel of the user"""
    available_reactions: Optional[
        list[Union[ReactionTypeEmoji, ReactionTypeCustomEmoji, ReactionTypePaid]]
    ] = None
    """*Optional*. List of available reactions allowed in the chat. If omitted, then all `emoji reactions <https://core.telegram.org/bots/api#reactiontypeemoji>`_ are allowed."""
    background_custom_emoji_id: Optional[str] = None
    """*Optional*. Custom emoji identifier of the emoji chosen by the chat for the reply header and link preview background"""
    profile_accent_color_id: Optional[int] = None
    """*Optional*. Identifier of the accent color for the chat's profile background. See `profile accent colors <https://core.telegram.org/bots/api#profile-accent-colors>`_ for more details."""
    profile_background_custom_emoji_id: Optional[str] = None
    """*Optional*. Custom emoji identifier of the emoji chosen by the chat for its profile background"""
    emoji_status_custom_emoji_id: Optional[str] = None
    """*Optional*. Custom emoji identifier of the emoji status of the chat or the other party in a private chat"""
    emoji_status_expiration_date: Optional[DateTime] = None
    """*Optional*. Expiration date of the emoji status of the chat or the other party in a private chat, in Unix time, if any"""
    bio: Optional[str] = None
    """*Optional*. Bio of the other party in a private chat"""
    has_private_forwards: Optional[bool] = None
    """*Optional*. :code:`True`, if privacy settings of the other party in the private chat allows to use :code:`tg://user?id=<user_id>` links only in chats with the user"""
    has_restricted_voice_and_video_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if the privacy settings of the other party restrict sending voice and video note messages in the private chat"""
    join_to_send_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if users need to join the supergroup before they can send messages"""
    join_by_request: Optional[bool] = None
    """*Optional*. :code:`True`, if all users directly joining the supergroup without using an invite link need to be approved by supergroup administrators"""
    description: Optional[str] = None
    """*Optional*. Description, for groups, supergroups and channel chats"""
    invite_link: Optional[str] = None
    """*Optional*. Primary invite link, for groups, supergroups and channel chats"""
    pinned_message: Optional[Message] = None
    """*Optional*. The most recent pinned message (by sending date)"""
    permissions: Optional[ChatPermissions] = None
    """*Optional*. Default chat member permissions, for groups and supergroups"""
    can_send_gift: Optional[bool] = None
    """*Optional*. :code:`True`, if gifts can be sent to the chat"""
    can_send_paid_media: Optional[bool] = None
    """*Optional*. :code:`True`, if paid media messages can be sent or forwarded to the channel chat. The field is available only for channel chats."""
    slow_mode_delay: Optional[int] = None
    """*Optional*. For supergroups, the minimum allowed delay between consecutive messages sent by each unprivileged user; in seconds"""
    unrestrict_boost_count: Optional[int] = None
    """*Optional*. For supergroups, the minimum number of boosts that a non-administrator user needs to add in order to ignore slow mode and chat permissions"""
    message_auto_delete_time: Optional[int] = None
    """*Optional*. The time after which all messages sent to the chat will be automatically deleted; in seconds"""
    has_aggressive_anti_spam_enabled: Optional[bool] = None
    """*Optional*. :code:`True`, if aggressive anti-spam checks are enabled in the supergroup. The field is only available to chat administrators."""
    has_hidden_members: Optional[bool] = None
    """*Optional*. :code:`True`, if non-administrators can only get the list of bots and administrators in the chat"""
    has_protected_content: Optional[bool] = None
    """*Optional*. :code:`True`, if messages from the chat can't be forwarded to other chats"""
    has_visible_history: Optional[bool] = None
    """*Optional*. :code:`True`, if new chat members will have access to old messages; available only to chat administrators"""
    sticker_set_name: Optional[str] = None
    """*Optional*. For supergroups, name of the group sticker set"""
    can_set_sticker_set: Optional[bool] = None
    """*Optional*. :code:`True`, if the bot can change the group sticker set"""
    custom_emoji_sticker_set_name: Optional[str] = None
    """*Optional*. For supergroups, the name of the group's custom emoji sticker set. Custom emoji from this set can be used by all users and bots in the group."""
    linked_chat_id: Optional[int] = None
    """*Optional*. Unique identifier for the linked chat, i.e. the discussion group identifier for a channel and vice versa; for supergroups and channel chats. This identifier may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier."""
    location: Optional[ChatLocation] = None
    """*Optional*. For supergroups, the location to which the supergroup is connected"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: int,
            type: str,
            accent_color_id: int,
            max_reaction_count: int,
            title: Optional[str] = None,
            username: Optional[str] = None,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            is_forum: Optional[bool] = None,
            photo: Optional[ChatPhoto] = None,
            active_usernames: Optional[list[str]] = None,
            birthdate: Optional[Birthdate] = None,
            business_intro: Optional[BusinessIntro] = None,
            business_location: Optional[BusinessLocation] = None,
            business_opening_hours: Optional[BusinessOpeningHours] = None,
            personal_chat: Optional[Chat] = None,
            available_reactions: Optional[
                list[Union[ReactionTypeEmoji, ReactionTypeCustomEmoji, ReactionTypePaid]]
            ] = None,
            background_custom_emoji_id: Optional[str] = None,
            profile_accent_color_id: Optional[int] = None,
            profile_background_custom_emoji_id: Optional[str] = None,
            emoji_status_custom_emoji_id: Optional[str] = None,
            emoji_status_expiration_date: Optional[DateTime] = None,
            bio: Optional[str] = None,
            has_private_forwards: Optional[bool] = None,
            has_restricted_voice_and_video_messages: Optional[bool] = None,
            join_to_send_messages: Optional[bool] = None,
            join_by_request: Optional[bool] = None,
            description: Optional[str] = None,
            invite_link: Optional[str] = None,
            pinned_message: Optional[Message] = None,
            permissions: Optional[ChatPermissions] = None,
            can_send_gift: Optional[bool] = None,
            can_send_paid_media: Optional[bool] = None,
            slow_mode_delay: Optional[int] = None,
            unrestrict_boost_count: Optional[int] = None,
            message_auto_delete_time: Optional[int] = None,
            has_aggressive_anti_spam_enabled: Optional[bool] = None,
            has_hidden_members: Optional[bool] = None,
            has_protected_content: Optional[bool] = None,
            has_visible_history: Optional[bool] = None,
            sticker_set_name: Optional[str] = None,
            can_set_sticker_set: Optional[bool] = None,
            custom_emoji_sticker_set_name: Optional[str] = None,
            linked_chat_id: Optional[int] = None,
            location: Optional[ChatLocation] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                id=id,
                type=type,
                accent_color_id=accent_color_id,
                max_reaction_count=max_reaction_count,
                title=title,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_forum=is_forum,
                photo=photo,
                active_usernames=active_usernames,
                birthdate=birthdate,
                business_intro=business_intro,
                business_location=business_location,
                business_opening_hours=business_opening_hours,
                personal_chat=personal_chat,
                available_reactions=available_reactions,
                background_custom_emoji_id=background_custom_emoji_id,
                profile_accent_color_id=profile_accent_color_id,
                profile_background_custom_emoji_id=profile_background_custom_emoji_id,
                emoji_status_custom_emoji_id=emoji_status_custom_emoji_id,
                emoji_status_expiration_date=emoji_status_expiration_date,
                bio=bio,
                has_private_forwards=has_private_forwards,
                has_restricted_voice_and_video_messages=has_restricted_voice_and_video_messages,
                join_to_send_messages=join_to_send_messages,
                join_by_request=join_by_request,
                description=description,
                invite_link=invite_link,
                pinned_message=pinned_message,
                permissions=permissions,
                can_send_gift=can_send_gift,
                can_send_paid_media=can_send_paid_media,
                slow_mode_delay=slow_mode_delay,
                unrestrict_boost_count=unrestrict_boost_count,
                message_auto_delete_time=message_auto_delete_time,
                has_aggressive_anti_spam_enabled=has_aggressive_anti_spam_enabled,
                has_hidden_members=has_hidden_members,
                has_protected_content=has_protected_content,
                has_visible_history=has_visible_history,
                sticker_set_name=sticker_set_name,
                can_set_sticker_set=can_set_sticker_set,
                custom_emoji_sticker_set_name=custom_emoji_sticker_set_name,
                linked_chat_id=linked_chat_id,
                location=location,
                **__pydantic_kwargs,
            )
