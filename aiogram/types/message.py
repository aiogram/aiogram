from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from pydantic import Field

from aiogram.utils.text_decorations import (
    TextDecoration,
    html_decoration,
    markdown_decoration,
)

from ..client.default import Default
from ..enums import ContentType
from .custom import DateTime
from .maybe_inaccessible_message import MaybeInaccessibleMessage
from .reply_parameters import ReplyParameters

if TYPE_CHECKING:
    from ..methods import (
        CopyMessage,
        DeleteMessage,
        EditMessageCaption,
        EditMessageLiveLocation,
        EditMessageMedia,
        EditMessageReplyMarkup,
        EditMessageText,
        ForwardMessage,
        PinChatMessage,
        SendAnimation,
        SendAudio,
        SendContact,
        SendDice,
        SendDocument,
        SendGame,
        SendInvoice,
        SendLocation,
        SendMediaGroup,
        SendMessage,
        SendPaidMedia,
        SendPhoto,
        SendPoll,
        SendSticker,
        SendVenue,
        SendVideo,
        SendVideoNote,
        SendVoice,
        SetMessageReaction,
        StopMessageLiveLocation,
        UnpinChatMessage,
    )
    from .animation import Animation
    from .audio import Audio
    from .chat import Chat
    from .chat_background import ChatBackground
    from .chat_boost_added import ChatBoostAdded
    from .chat_shared import ChatShared
    from .contact import Contact
    from .dice import Dice
    from .document import Document
    from .external_reply_info import ExternalReplyInfo
    from .force_reply import ForceReply
    from .forum_topic_closed import ForumTopicClosed
    from .forum_topic_created import ForumTopicCreated
    from .forum_topic_edited import ForumTopicEdited
    from .forum_topic_reopened import ForumTopicReopened
    from .game import Game
    from .general_forum_topic_hidden import GeneralForumTopicHidden
    from .general_forum_topic_unhidden import GeneralForumTopicUnhidden
    from .giveaway import Giveaway
    from .giveaway_completed import GiveawayCompleted
    from .giveaway_created import GiveawayCreated
    from .giveaway_winners import GiveawayWinners
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_file import InputFile
    from .input_media_audio import InputMediaAudio
    from .input_media_document import InputMediaDocument
    from .input_media_photo import InputMediaPhoto
    from .input_media_union import InputMediaUnion
    from .input_media_video import InputMediaVideo
    from .input_paid_media_union import InputPaidMediaUnion
    from .input_poll_option import InputPollOption
    from .invoice import Invoice
    from .labeled_price import LabeledPrice
    from .link_preview_options import LinkPreviewOptions
    from .location import Location
    from .maybe_inaccessible_message_union import MaybeInaccessibleMessageUnion
    from .message_auto_delete_timer_changed import MessageAutoDeleteTimerChanged
    from .message_entity import MessageEntity
    from .message_origin_union import MessageOriginUnion
    from .paid_media_info import PaidMediaInfo
    from .passport_data import PassportData
    from .photo_size import PhotoSize
    from .poll import Poll
    from .proximity_alert_triggered import ProximityAlertTriggered
    from .reaction_type_union import ReactionTypeUnion
    from .refunded_payment import RefundedPayment
    from .reply_keyboard_markup import ReplyKeyboardMarkup
    from .reply_keyboard_remove import ReplyKeyboardRemove
    from .sticker import Sticker
    from .story import Story
    from .successful_payment import SuccessfulPayment
    from .text_quote import TextQuote
    from .user import User
    from .user_shared import UserShared
    from .users_shared import UsersShared
    from .venue import Venue
    from .video import Video
    from .video_chat_ended import VideoChatEnded
    from .video_chat_participants_invited import VideoChatParticipantsInvited
    from .video_chat_scheduled import VideoChatScheduled
    from .video_chat_started import VideoChatStarted
    from .video_note import VideoNote
    from .voice import Voice
    from .web_app_data import WebAppData
    from .write_access_allowed import WriteAccessAllowed


class Message(MaybeInaccessibleMessage):
    """
    This object represents a message.

    Source: https://core.telegram.org/bots/api#message
    """

    message_id: int
    """Unique message identifier inside this chat. In specific instances (e.g., message containing a video sent to a big chat), the server might automatically schedule a message instead of sending it immediately. In such cases, this field will be 0 and the relevant message will be unusable until it is actually sent"""
    date: DateTime
    """Date the message was sent in Unix time. It is always a positive number, representing a valid date."""
    chat: Chat
    """Chat the message belongs to"""
    message_thread_id: Optional[int] = None
    """*Optional*. Unique identifier of a message thread to which the message belongs; for supergroups only"""
    from_user: Optional[User] = Field(None, alias="from")
    """*Optional*. Sender of the message; may be empty for messages sent to channels. For backward compatibility, if the message was sent on behalf of a chat, the field contains a fake sender user in non-channel chats"""
    sender_chat: Optional[Chat] = None
    """*Optional*. Sender of the message when sent on behalf of a chat. For example, the supergroup itself for messages sent by its anonymous administrators or a linked channel for messages automatically forwarded to the channel's discussion group. For backward compatibility, if the message was sent on behalf of a chat, the field *from* contains a fake sender user in non-channel chats."""
    sender_boost_count: Optional[int] = None
    """*Optional*. If the sender of the message boosted the chat, the number of boosts added by the user"""
    sender_business_bot: Optional[User] = None
    """*Optional*. The bot that actually sent the message on behalf of the business account. Available only for outgoing messages sent on behalf of the connected business account."""
    business_connection_id: Optional[str] = None
    """*Optional*. Unique identifier of the business connection from which the message was received. If non-empty, the message belongs to a chat of the corresponding business account that is independent from any potential bot chat which might share the same identifier."""
    forward_origin: Optional[MessageOriginUnion] = None
    """*Optional*. Information about the original message for forwarded messages"""
    is_topic_message: Optional[bool] = None
    """*Optional*. :code:`True`, if the message is sent to a forum topic"""
    is_automatic_forward: Optional[bool] = None
    """*Optional*. :code:`True`, if the message is a channel post that was automatically forwarded to the connected discussion group"""
    reply_to_message: Optional[Message] = None
    """*Optional*. For replies in the same chat and message thread, the original message. Note that the Message object in this field will not contain further *reply_to_message* fields even if it itself is a reply."""
    external_reply: Optional[ExternalReplyInfo] = None
    """*Optional*. Information about the message that is being replied to, which may come from another chat or forum topic"""
    quote: Optional[TextQuote] = None
    """*Optional*. For replies that quote part of the original message, the quoted part of the message"""
    reply_to_story: Optional[Story] = None
    """*Optional*. For replies to a story, the original story"""
    via_bot: Optional[User] = None
    """*Optional*. Bot through which the message was sent"""
    edit_date: Optional[int] = None
    """*Optional*. Date the message was last edited in Unix time"""
    has_protected_content: Optional[bool] = None
    """*Optional*. :code:`True`, if the message can't be forwarded"""
    is_from_offline: Optional[bool] = None
    """*Optional*. True, if the message was sent by an implicit action, for example, as an away or a greeting business message, or as a scheduled message"""
    media_group_id: Optional[str] = None
    """*Optional*. The unique identifier of a media message group this message belongs to"""
    author_signature: Optional[str] = None
    """*Optional*. Signature of the post author for messages in channels, or the custom title of an anonymous group administrator"""
    text: Optional[str] = None
    """*Optional*. For text messages, the actual UTF-8 text of the message"""
    entities: Optional[list[MessageEntity]] = None
    """*Optional*. For text messages, special entities like usernames, URLs, bot commands, etc. that appear in the text"""
    link_preview_options: Optional[LinkPreviewOptions] = None
    """*Optional*. Options used for link preview generation for the message, if it is a text message and link preview options were changed"""
    effect_id: Optional[str] = None
    """*Optional*. Unique identifier of the message effect added to the message"""
    animation: Optional[Animation] = None
    """*Optional*. Message is an animation, information about the animation. For backward compatibility, when this field is set, the *document* field will also be set"""
    audio: Optional[Audio] = None
    """*Optional*. Message is an audio file, information about the file"""
    document: Optional[Document] = None
    """*Optional*. Message is a general file, information about the file"""
    paid_media: Optional[PaidMediaInfo] = None
    """*Optional*. Message contains paid media; information about the paid media"""
    photo: Optional[list[PhotoSize]] = None
    """*Optional*. Message is a photo, available sizes of the photo"""
    sticker: Optional[Sticker] = None
    """*Optional*. Message is a sticker, information about the sticker"""
    story: Optional[Story] = None
    """*Optional*. Message is a forwarded story"""
    video: Optional[Video] = None
    """*Optional*. Message is a video, information about the video"""
    video_note: Optional[VideoNote] = None
    """*Optional*. Message is a `video note <https://telegram.org/blog/video-messages-and-telescope>`_, information about the video message"""
    voice: Optional[Voice] = None
    """*Optional*. Message is a voice message, information about the file"""
    caption: Optional[str] = None
    """*Optional*. Caption for the animation, audio, document, paid media, photo, video or voice"""
    caption_entities: Optional[list[MessageEntity]] = None
    """*Optional*. For messages with a caption, special entities like usernames, URLs, bot commands, etc. that appear in the caption"""
    show_caption_above_media: Optional[bool] = None
    """*Optional*. True, if the caption must be shown above the message media"""
    has_media_spoiler: Optional[bool] = None
    """*Optional*. :code:`True`, if the message media is covered by a spoiler animation"""
    contact: Optional[Contact] = None
    """*Optional*. Message is a shared contact, information about the contact"""
    dice: Optional[Dice] = None
    """*Optional*. Message is a dice with random value"""
    game: Optional[Game] = None
    """*Optional*. Message is a game, information about the game. `More about games » <https://core.telegram.org/bots/api#games>`_"""
    poll: Optional[Poll] = None
    """*Optional*. Message is a native poll, information about the poll"""
    venue: Optional[Venue] = None
    """*Optional*. Message is a venue, information about the venue. For backward compatibility, when this field is set, the *location* field will also be set"""
    location: Optional[Location] = None
    """*Optional*. Message is a shared location, information about the location"""
    new_chat_members: Optional[list[User]] = None
    """*Optional*. New members that were added to the group or supergroup and information about them (the bot itself may be one of these members)"""
    left_chat_member: Optional[User] = None
    """*Optional*. A member was removed from the group, information about them (this member may be the bot itself)"""
    new_chat_title: Optional[str] = None
    """*Optional*. A chat title was changed to this value"""
    new_chat_photo: Optional[list[PhotoSize]] = None
    """*Optional*. A chat photo was change to this value"""
    delete_chat_photo: Optional[bool] = None
    """*Optional*. Service message: the chat photo was deleted"""
    group_chat_created: Optional[bool] = None
    """*Optional*. Service message: the group has been created"""
    supergroup_chat_created: Optional[bool] = None
    """*Optional*. Service message: the supergroup has been created. This field can't be received in a message coming through updates, because bot can't be a member of a supergroup when it is created. It can only be found in reply_to_message if someone replies to a very first message in a directly created supergroup."""
    channel_chat_created: Optional[bool] = None
    """*Optional*. Service message: the channel has been created. This field can't be received in a message coming through updates, because bot can't be a member of a channel when it is created. It can only be found in reply_to_message if someone replies to a very first message in a channel."""
    message_auto_delete_timer_changed: Optional[MessageAutoDeleteTimerChanged] = None
    """*Optional*. Service message: auto-delete timer settings changed in the chat"""
    migrate_to_chat_id: Optional[int] = None
    """*Optional*. The group has been migrated to a supergroup with the specified identifier. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this identifier."""
    migrate_from_chat_id: Optional[int] = None
    """*Optional*. The supergroup has been migrated from a group with the specified identifier. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this identifier."""
    pinned_message: Optional[MaybeInaccessibleMessageUnion] = None
    """*Optional*. Specified message was pinned. Note that the Message object in this field will not contain further *reply_to_message* fields even if it itself is a reply."""
    invoice: Optional[Invoice] = None
    """*Optional*. Message is an invoice for a `payment <https://core.telegram.org/bots/api#payments>`_, information about the invoice. `More about payments » <https://core.telegram.org/bots/api#payments>`_"""
    successful_payment: Optional[SuccessfulPayment] = None
    """*Optional*. Message is a service message about a successful payment, information about the payment. `More about payments » <https://core.telegram.org/bots/api#payments>`_"""
    refunded_payment: Optional[RefundedPayment] = None
    """*Optional*. Message is a service message about a refunded payment, information about the payment. `More about payments » <https://core.telegram.org/bots/api#payments>`_"""
    users_shared: Optional[UsersShared] = None
    """*Optional*. Service message: users were shared with the bot"""
    chat_shared: Optional[ChatShared] = None
    """*Optional*. Service message: a chat was shared with the bot"""
    connected_website: Optional[str] = None
    """*Optional*. The domain name of the website on which the user has logged in. `More about Telegram Login » <https://core.telegram.org/widgets/login>`_"""
    write_access_allowed: Optional[WriteAccessAllowed] = None
    """*Optional*. Service message: the user allowed the bot to write messages after adding it to the attachment or side menu, launching a Web App from a link, or accepting an explicit request from a Web App sent by the method `requestWriteAccess <https://core.telegram.org/bots/webapps#initializing-mini-apps>`_"""
    passport_data: Optional[PassportData] = None
    """*Optional*. Telegram Passport data"""
    proximity_alert_triggered: Optional[ProximityAlertTriggered] = None
    """*Optional*. Service message. A user in the chat triggered another user's proximity alert while sharing Live Location."""
    boost_added: Optional[ChatBoostAdded] = None
    """*Optional*. Service message: user boosted the chat"""
    chat_background_set: Optional[ChatBackground] = None
    """*Optional*. Service message: chat background set"""
    forum_topic_created: Optional[ForumTopicCreated] = None
    """*Optional*. Service message: forum topic created"""
    forum_topic_edited: Optional[ForumTopicEdited] = None
    """*Optional*. Service message: forum topic edited"""
    forum_topic_closed: Optional[ForumTopicClosed] = None
    """*Optional*. Service message: forum topic closed"""
    forum_topic_reopened: Optional[ForumTopicReopened] = None
    """*Optional*. Service message: forum topic reopened"""
    general_forum_topic_hidden: Optional[GeneralForumTopicHidden] = None
    """*Optional*. Service message: the 'General' forum topic hidden"""
    general_forum_topic_unhidden: Optional[GeneralForumTopicUnhidden] = None
    """*Optional*. Service message: the 'General' forum topic unhidden"""
    giveaway_created: Optional[GiveawayCreated] = None
    """*Optional*. Service message: a scheduled giveaway was created"""
    giveaway: Optional[Giveaway] = None
    """*Optional*. The message is a scheduled giveaway message"""
    giveaway_winners: Optional[GiveawayWinners] = None
    """*Optional*. A giveaway with public winners was completed"""
    giveaway_completed: Optional[GiveawayCompleted] = None
    """*Optional*. Service message: a giveaway without public winners was completed"""
    video_chat_scheduled: Optional[VideoChatScheduled] = None
    """*Optional*. Service message: video chat scheduled"""
    video_chat_started: Optional[VideoChatStarted] = None
    """*Optional*. Service message: video chat started"""
    video_chat_ended: Optional[VideoChatEnded] = None
    """*Optional*. Service message: video chat ended"""
    video_chat_participants_invited: Optional[VideoChatParticipantsInvited] = None
    """*Optional*. Service message: new participants invited to a video chat"""
    web_app_data: Optional[WebAppData] = None
    """*Optional*. Service message: data sent by a Web App"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """*Optional*. Inline keyboard attached to the message. :code:`login_url` buttons are represented as ordinary :code:`url` buttons."""
    forward_date: Optional[DateTime] = Field(None, json_schema_extra={"deprecated": True})
    """*Optional*. For forwarded messages, date the original message was sent in Unix time

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""
    forward_from: Optional[User] = Field(None, json_schema_extra={"deprecated": True})
    """*Optional*. For forwarded messages, sender of the original message

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""
    forward_from_chat: Optional[Chat] = Field(None, json_schema_extra={"deprecated": True})
    """*Optional*. For messages forwarded from channels or from anonymous administrators, information about the original sender chat

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""
    forward_from_message_id: Optional[int] = Field(None, json_schema_extra={"deprecated": True})
    """*Optional*. For messages forwarded from channels, identifier of the original message in the channel

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""
    forward_sender_name: Optional[str] = Field(None, json_schema_extra={"deprecated": True})
    """*Optional*. Sender's name for messages forwarded from users who disallow adding a link to their account in forwarded messages

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""
    forward_signature: Optional[str] = Field(None, json_schema_extra={"deprecated": True})
    """*Optional*. For forwarded messages that were originally sent in channels or by an anonymous chat administrator, signature of the message sender if present

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""
    user_shared: Optional[UserShared] = Field(None, json_schema_extra={"deprecated": True})
    """*Optional*. Service message: a user was shared with the bot

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            message_id: int,
            date: DateTime,
            chat: Chat,
            message_thread_id: Optional[int] = None,
            from_user: Optional[User] = None,
            sender_chat: Optional[Chat] = None,
            sender_boost_count: Optional[int] = None,
            sender_business_bot: Optional[User] = None,
            business_connection_id: Optional[str] = None,
            forward_origin: Optional[MessageOriginUnion] = None,
            is_topic_message: Optional[bool] = None,
            is_automatic_forward: Optional[bool] = None,
            reply_to_message: Optional[Message] = None,
            external_reply: Optional[ExternalReplyInfo] = None,
            quote: Optional[TextQuote] = None,
            reply_to_story: Optional[Story] = None,
            via_bot: Optional[User] = None,
            edit_date: Optional[int] = None,
            has_protected_content: Optional[bool] = None,
            is_from_offline: Optional[bool] = None,
            media_group_id: Optional[str] = None,
            author_signature: Optional[str] = None,
            text: Optional[str] = None,
            entities: Optional[list[MessageEntity]] = None,
            link_preview_options: Optional[LinkPreviewOptions] = None,
            effect_id: Optional[str] = None,
            animation: Optional[Animation] = None,
            audio: Optional[Audio] = None,
            document: Optional[Document] = None,
            paid_media: Optional[PaidMediaInfo] = None,
            photo: Optional[list[PhotoSize]] = None,
            sticker: Optional[Sticker] = None,
            story: Optional[Story] = None,
            video: Optional[Video] = None,
            video_note: Optional[VideoNote] = None,
            voice: Optional[Voice] = None,
            caption: Optional[str] = None,
            caption_entities: Optional[list[MessageEntity]] = None,
            show_caption_above_media: Optional[bool] = None,
            has_media_spoiler: Optional[bool] = None,
            contact: Optional[Contact] = None,
            dice: Optional[Dice] = None,
            game: Optional[Game] = None,
            poll: Optional[Poll] = None,
            venue: Optional[Venue] = None,
            location: Optional[Location] = None,
            new_chat_members: Optional[list[User]] = None,
            left_chat_member: Optional[User] = None,
            new_chat_title: Optional[str] = None,
            new_chat_photo: Optional[list[PhotoSize]] = None,
            delete_chat_photo: Optional[bool] = None,
            group_chat_created: Optional[bool] = None,
            supergroup_chat_created: Optional[bool] = None,
            channel_chat_created: Optional[bool] = None,
            message_auto_delete_timer_changed: Optional[MessageAutoDeleteTimerChanged] = None,
            migrate_to_chat_id: Optional[int] = None,
            migrate_from_chat_id: Optional[int] = None,
            pinned_message: Optional[MaybeInaccessibleMessageUnion] = None,
            invoice: Optional[Invoice] = None,
            successful_payment: Optional[SuccessfulPayment] = None,
            refunded_payment: Optional[RefundedPayment] = None,
            users_shared: Optional[UsersShared] = None,
            chat_shared: Optional[ChatShared] = None,
            connected_website: Optional[str] = None,
            write_access_allowed: Optional[WriteAccessAllowed] = None,
            passport_data: Optional[PassportData] = None,
            proximity_alert_triggered: Optional[ProximityAlertTriggered] = None,
            boost_added: Optional[ChatBoostAdded] = None,
            chat_background_set: Optional[ChatBackground] = None,
            forum_topic_created: Optional[ForumTopicCreated] = None,
            forum_topic_edited: Optional[ForumTopicEdited] = None,
            forum_topic_closed: Optional[ForumTopicClosed] = None,
            forum_topic_reopened: Optional[ForumTopicReopened] = None,
            general_forum_topic_hidden: Optional[GeneralForumTopicHidden] = None,
            general_forum_topic_unhidden: Optional[GeneralForumTopicUnhidden] = None,
            giveaway_created: Optional[GiveawayCreated] = None,
            giveaway: Optional[Giveaway] = None,
            giveaway_winners: Optional[GiveawayWinners] = None,
            giveaway_completed: Optional[GiveawayCompleted] = None,
            video_chat_scheduled: Optional[VideoChatScheduled] = None,
            video_chat_started: Optional[VideoChatStarted] = None,
            video_chat_ended: Optional[VideoChatEnded] = None,
            video_chat_participants_invited: Optional[VideoChatParticipantsInvited] = None,
            web_app_data: Optional[WebAppData] = None,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            forward_date: Optional[DateTime] = None,
            forward_from: Optional[User] = None,
            forward_from_chat: Optional[Chat] = None,
            forward_from_message_id: Optional[int] = None,
            forward_sender_name: Optional[str] = None,
            forward_signature: Optional[str] = None,
            user_shared: Optional[UserShared] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                message_id=message_id,
                date=date,
                chat=chat,
                message_thread_id=message_thread_id,
                from_user=from_user,
                sender_chat=sender_chat,
                sender_boost_count=sender_boost_count,
                sender_business_bot=sender_business_bot,
                business_connection_id=business_connection_id,
                forward_origin=forward_origin,
                is_topic_message=is_topic_message,
                is_automatic_forward=is_automatic_forward,
                reply_to_message=reply_to_message,
                external_reply=external_reply,
                quote=quote,
                reply_to_story=reply_to_story,
                via_bot=via_bot,
                edit_date=edit_date,
                has_protected_content=has_protected_content,
                is_from_offline=is_from_offline,
                media_group_id=media_group_id,
                author_signature=author_signature,
                text=text,
                entities=entities,
                link_preview_options=link_preview_options,
                effect_id=effect_id,
                animation=animation,
                audio=audio,
                document=document,
                paid_media=paid_media,
                photo=photo,
                sticker=sticker,
                story=story,
                video=video,
                video_note=video_note,
                voice=voice,
                caption=caption,
                caption_entities=caption_entities,
                show_caption_above_media=show_caption_above_media,
                has_media_spoiler=has_media_spoiler,
                contact=contact,
                dice=dice,
                game=game,
                poll=poll,
                venue=venue,
                location=location,
                new_chat_members=new_chat_members,
                left_chat_member=left_chat_member,
                new_chat_title=new_chat_title,
                new_chat_photo=new_chat_photo,
                delete_chat_photo=delete_chat_photo,
                group_chat_created=group_chat_created,
                supergroup_chat_created=supergroup_chat_created,
                channel_chat_created=channel_chat_created,
                message_auto_delete_timer_changed=message_auto_delete_timer_changed,
                migrate_to_chat_id=migrate_to_chat_id,
                migrate_from_chat_id=migrate_from_chat_id,
                pinned_message=pinned_message,
                invoice=invoice,
                successful_payment=successful_payment,
                refunded_payment=refunded_payment,
                users_shared=users_shared,
                chat_shared=chat_shared,
                connected_website=connected_website,
                write_access_allowed=write_access_allowed,
                passport_data=passport_data,
                proximity_alert_triggered=proximity_alert_triggered,
                boost_added=boost_added,
                chat_background_set=chat_background_set,
                forum_topic_created=forum_topic_created,
                forum_topic_edited=forum_topic_edited,
                forum_topic_closed=forum_topic_closed,
                forum_topic_reopened=forum_topic_reopened,
                general_forum_topic_hidden=general_forum_topic_hidden,
                general_forum_topic_unhidden=general_forum_topic_unhidden,
                giveaway_created=giveaway_created,
                giveaway=giveaway,
                giveaway_winners=giveaway_winners,
                giveaway_completed=giveaway_completed,
                video_chat_scheduled=video_chat_scheduled,
                video_chat_started=video_chat_started,
                video_chat_ended=video_chat_ended,
                video_chat_participants_invited=video_chat_participants_invited,
                web_app_data=web_app_data,
                reply_markup=reply_markup,
                forward_date=forward_date,
                forward_from=forward_from,
                forward_from_chat=forward_from_chat,
                forward_from_message_id=forward_from_message_id,
                forward_sender_name=forward_sender_name,
                forward_signature=forward_signature,
                user_shared=user_shared,
                **__pydantic_kwargs,
            )

    @property
    def content_type(self) -> str:
        if self.text:
            return ContentType.TEXT
        if self.audio:
            return ContentType.AUDIO
        if self.animation:
            return ContentType.ANIMATION
        if self.document:
            return ContentType.DOCUMENT
        if self.game:
            return ContentType.GAME
        if self.photo:
            return ContentType.PHOTO
        if self.sticker:
            return ContentType.STICKER
        if self.video:
            return ContentType.VIDEO
        if self.video_note:
            return ContentType.VIDEO_NOTE
        if self.voice:
            return ContentType.VOICE
        if self.contact:
            return ContentType.CONTACT
        if self.venue:
            return ContentType.VENUE
        if self.location:
            return ContentType.LOCATION
        if self.new_chat_members:
            return ContentType.NEW_CHAT_MEMBERS
        if self.left_chat_member:
            return ContentType.LEFT_CHAT_MEMBER
        if self.invoice:
            return ContentType.INVOICE
        if self.successful_payment:
            return ContentType.SUCCESSFUL_PAYMENT
        if self.users_shared:
            return ContentType.USERS_SHARED
        if self.connected_website:
            return ContentType.CONNECTED_WEBSITE
        if self.migrate_from_chat_id:
            return ContentType.MIGRATE_FROM_CHAT_ID
        if self.migrate_to_chat_id:
            return ContentType.MIGRATE_TO_CHAT_ID
        if self.pinned_message:
            return ContentType.PINNED_MESSAGE
        if self.new_chat_title:
            return ContentType.NEW_CHAT_TITLE
        if self.new_chat_photo:
            return ContentType.NEW_CHAT_PHOTO
        if self.delete_chat_photo:
            return ContentType.DELETE_CHAT_PHOTO
        if self.group_chat_created:
            return ContentType.GROUP_CHAT_CREATED
        if self.supergroup_chat_created:
            return ContentType.SUPERGROUP_CHAT_CREATED
        if self.channel_chat_created:
            return ContentType.CHANNEL_CHAT_CREATED
        if self.paid_media:
            return ContentType.PAID_MEDIA
        if self.passport_data:
            return ContentType.PASSPORT_DATA
        if self.proximity_alert_triggered:
            return ContentType.PROXIMITY_ALERT_TRIGGERED
        if self.poll:
            return ContentType.POLL
        if self.dice:
            return ContentType.DICE
        if self.message_auto_delete_timer_changed:
            return ContentType.MESSAGE_AUTO_DELETE_TIMER_CHANGED
        if self.forum_topic_created:
            return ContentType.FORUM_TOPIC_CREATED
        if self.forum_topic_edited:
            return ContentType.FORUM_TOPIC_EDITED
        if self.forum_topic_closed:
            return ContentType.FORUM_TOPIC_CLOSED
        if self.forum_topic_reopened:
            return ContentType.FORUM_TOPIC_REOPENED
        if self.general_forum_topic_hidden:
            return ContentType.GENERAL_FORUM_TOPIC_HIDDEN
        if self.general_forum_topic_unhidden:
            return ContentType.GENERAL_FORUM_TOPIC_UNHIDDEN
        if self.giveaway_created:
            return ContentType.GIVEAWAY_CREATED
        if self.giveaway:
            return ContentType.GIVEAWAY
        if self.giveaway_completed:
            return ContentType.GIVEAWAY_COMPLETED
        if self.giveaway_winners:
            return ContentType.GIVEAWAY_WINNERS
        if self.video_chat_scheduled:
            return ContentType.VIDEO_CHAT_SCHEDULED
        if self.video_chat_started:
            return ContentType.VIDEO_CHAT_STARTED
        if self.video_chat_ended:
            return ContentType.VIDEO_CHAT_ENDED
        if self.video_chat_participants_invited:
            return ContentType.VIDEO_CHAT_PARTICIPANTS_INVITED
        if self.web_app_data:
            return ContentType.WEB_APP_DATA
        if self.user_shared:
            return ContentType.USER_SHARED
        if self.chat_shared:
            return ContentType.CHAT_SHARED
        if self.story:
            return ContentType.STORY
        if self.write_access_allowed:
            return ContentType.WRITE_ACCESS_ALLOWED
        if self.chat_background_set:
            return ContentType.CHAT_BACKGROUND_SET
        if self.boost_added:
            return ContentType.BOOST_ADDED
        if self.refunded_payment:
            return ContentType.REFUNDED_PAYMENT

        return ContentType.UNKNOWN

    def _unparse_entities(self, text_decoration: TextDecoration) -> str:
        text = self.text or self.caption or ""
        entities = self.entities or self.caption_entities or []
        return text_decoration.unparse(text=text, entities=entities)

    @property
    def html_text(self) -> str:
        return self._unparse_entities(html_decoration)

    @property
    def md_text(self) -> str:
        return self._unparse_entities(markdown_decoration)

    def as_reply_parameters(
        self,
        allow_sending_without_reply: Optional[Union[bool, Default]] = Default(
            "allow_sending_without_reply"
        ),
        quote: Optional[str] = None,
        quote_parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        quote_entities: Optional[List[MessageEntity]] = None,
        quote_position: Optional[int] = None,
    ) -> ReplyParameters:
        return ReplyParameters(
            message_id=self.message_id,
            chat_id=self.chat.id,
            allow_sending_without_reply=allow_sending_without_reply,
            quote=quote,
            quote_parse_mode=quote_parse_mode,
            quote_entities=quote_entities,
            quote_position=quote_position,
        )

    def reply_animation(
        self,
        animation: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumbnail: Optional[InputFile] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        show_caption_above_media: Optional[Union[bool, Default]] = Default(
            "show_caption_above_media"
        ),
        has_spoiler: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendAnimation:
        """
        Shortcut for method :class:`aiogram.methods.send_animation.SendAnimation`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendanimation

        :param animation: Animation to send. Pass a file_id as String to send an animation that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation from the Internet, or upload a new animation using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param duration: Duration of sent animation in seconds
        :param width: Animation width
        :param height: Animation height
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Animation caption (may also be used when resending animation by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the animation caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True`, if the caption must be shown above the message media
        :param has_spoiler: Pass :code:`True` if the animation needs to be covered with a spoiler animation
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_animation.SendAnimation`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendAnimation

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendAnimation(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            animation=animation,
            duration=duration,
            width=width,
            height=height,
            thumbnail=thumbnail,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            has_spoiler=has_spoiler,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_animation(
        self,
        animation: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumbnail: Optional[InputFile] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        show_caption_above_media: Optional[Union[bool, Default]] = Default(
            "show_caption_above_media"
        ),
        has_spoiler: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendAnimation:
        """
        Shortcut for method :class:`aiogram.methods.send_animation.SendAnimation`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendanimation

        :param animation: Animation to send. Pass a file_id as String to send an animation that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation from the Internet, or upload a new animation using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param duration: Duration of sent animation in seconds
        :param width: Animation width
        :param height: Animation height
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Animation caption (may also be used when resending animation by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the animation caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True`, if the caption must be shown above the message media
        :param has_spoiler: Pass :code:`True` if the animation needs to be covered with a spoiler animation
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_animation.SendAnimation`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendAnimation

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendAnimation(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            animation=animation,
            duration=duration,
            width=width,
            height=height,
            thumbnail=thumbnail,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            has_spoiler=has_spoiler,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_audio(
        self,
        audio: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        thumbnail: Optional[InputFile] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendAudio:
        """
        Shortcut for method :class:`aiogram.methods.send_audio.SendAudio`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .MP3 or .M4A format. On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.
        For sending voice messages, use the :class:`aiogram.methods.send_voice.SendVoice` method instead.

        Source: https://core.telegram.org/bots/api#sendaudio

        :param audio: Audio file to send. Pass a file_id as String to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an audio file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Audio caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the audio caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param duration: Duration of the audio in seconds
        :param performer: Performer
        :param title: Track name
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_audio.SendAudio`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendAudio

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendAudio(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            audio=audio,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            performer=performer,
            title=title,
            thumbnail=thumbnail,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_audio(
        self,
        audio: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        thumbnail: Optional[InputFile] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendAudio:
        """
        Shortcut for method :class:`aiogram.methods.send_audio.SendAudio`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .MP3 or .M4A format. On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.
        For sending voice messages, use the :class:`aiogram.methods.send_voice.SendVoice` method instead.

        Source: https://core.telegram.org/bots/api#sendaudio

        :param audio: Audio file to send. Pass a file_id as String to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an audio file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Audio caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the audio caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param duration: Duration of the audio in seconds
        :param performer: Performer
        :param title: Track name
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_audio.SendAudio`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendAudio

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendAudio(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            audio=audio,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            performer=performer,
            title=title,
            thumbnail=thumbnail,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_contact(
        self,
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        vcard: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendContact:
        """
        Shortcut for method :class:`aiogram.methods.send_contact.SendContact`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send phone contacts. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendcontact

        :param phone_number: Contact's phone number
        :param first_name: Contact's first name
        :param last_name: Contact's last name
        :param vcard: Additional data about the contact in the form of a `vCard <https://en.wikipedia.org/wiki/VCard>`_, 0-2048 bytes
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_contact.SendContact`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendContact

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendContact(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            vcard=vcard,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_contact(
        self,
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        vcard: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendContact:
        """
        Shortcut for method :class:`aiogram.methods.send_contact.SendContact`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send phone contacts. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendcontact

        :param phone_number: Contact's phone number
        :param first_name: Contact's first name
        :param last_name: Contact's last name
        :param vcard: Additional data about the contact in the form of a `vCard <https://en.wikipedia.org/wiki/VCard>`_, 0-2048 bytes
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_contact.SendContact`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendContact

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendContact(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            vcard=vcard,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_document(
        self,
        document: Union[InputFile, str],
        thumbnail: Optional[InputFile] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        disable_content_type_detection: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendDocument:
        """
        Shortcut for method :class:`aiogram.methods.send_document.SendDocument`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send general files. On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#senddocument

        :param document: File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Document caption (may also be used when resending documents by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the document caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param disable_content_type_detection: Disables automatic server-side content type detection for files uploaded using multipart/form-data
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_document.SendDocument`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendDocument

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendDocument(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            document=document,
            thumbnail=thumbnail,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_content_type_detection=disable_content_type_detection,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_document(
        self,
        document: Union[InputFile, str],
        thumbnail: Optional[InputFile] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        disable_content_type_detection: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendDocument:
        """
        Shortcut for method :class:`aiogram.methods.send_document.SendDocument`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send general files. On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#senddocument

        :param document: File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Document caption (may also be used when resending documents by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the document caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param disable_content_type_detection: Disables automatic server-side content type detection for files uploaded using multipart/form-data
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_document.SendDocument`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendDocument

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendDocument(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            document=document,
            thumbnail=thumbnail,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_content_type_detection=disable_content_type_detection,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_game(
        self,
        game_short_name: str,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendGame:
        """
        Shortcut for method :class:`aiogram.methods.send_game.SendGame`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send a game. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendgame

        :param game_short_name: Short name of the game, serves as the unique identifier for the game. Set up your games via `@BotFather <https://t.me/botfather>`_.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_. If empty, one 'Play game_title' button will be shown. If not empty, the first button must launch the game.
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_game.SendGame`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendGame

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendGame(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            game_short_name=game_short_name,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_game(
        self,
        game_short_name: str,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendGame:
        """
        Shortcut for method :class:`aiogram.methods.send_game.SendGame`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send a game. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendgame

        :param game_short_name: Short name of the game, serves as the unique identifier for the game. Set up your games via `@BotFather <https://t.me/botfather>`_.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_. If empty, one 'Play game_title' button will be shown. If not empty, the first button must launch the game.
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_game.SendGame`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendGame

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendGame(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            game_short_name=game_short_name,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_invoice(
        self,
        title: str,
        description: str,
        payload: str,
        currency: str,
        prices: list[LabeledPrice],
        provider_token: Optional[str] = None,
        max_tip_amount: Optional[int] = None,
        suggested_tip_amounts: Optional[list[int]] = None,
        start_parameter: Optional[str] = None,
        provider_data: Optional[str] = None,
        photo_url: Optional[str] = None,
        photo_size: Optional[int] = None,
        photo_width: Optional[int] = None,
        photo_height: Optional[int] = None,
        need_name: Optional[bool] = None,
        need_phone_number: Optional[bool] = None,
        need_email: Optional[bool] = None,
        need_shipping_address: Optional[bool] = None,
        send_phone_number_to_provider: Optional[bool] = None,
        send_email_to_provider: Optional[bool] = None,
        is_flexible: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendInvoice:
        """
        Shortcut for method :class:`aiogram.methods.send_invoice.SendInvoice`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send invoices. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendinvoice

        :param title: Product name, 1-32 characters
        :param description: Product description, 1-255 characters
        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use it for your internal processes.
        :param currency: Three-letter ISO 4217 currency code, see `more on currencies <https://core.telegram.org/bots/payments#supported-currencies>`_. Pass 'XTR' for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param prices: Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.). Must contain exactly one item for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param provider_token: Payment provider token, obtained via `@BotFather <https://t.me/botfather>`_. Pass an empty string for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param max_tip_amount: The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of :code:`US$ 1.45` pass :code:`max_tip_amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0. Not supported for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*.
        :param start_parameter: Unique deep-linking parameter. If left empty, **forwarded copies** of the sent message will have a *Pay* button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a *URL* button with a deep link to the bot (instead of a *Pay* button), with the value used as the start parameter
        :param provider_data: JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.
        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.
        :param photo_size: Photo size in bytes
        :param photo_width: Photo width
        :param photo_height: Photo height
        :param need_name: Pass :code:`True` if you require the user's full name to complete the order. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param need_phone_number: Pass :code:`True` if you require the user's phone number to complete the order. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param need_email: Pass :code:`True` if you require the user's email address to complete the order. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param need_shipping_address: Pass :code:`True` if you require the user's shipping address to complete the order. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param send_phone_number_to_provider: Pass :code:`True` if the user's phone number should be sent to the provider. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param send_email_to_provider: Pass :code:`True` if the user's email address should be sent to the provider. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param is_flexible: Pass :code:`True` if the final price depends on the shipping method. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_. If empty, one 'Pay :code:`total price`' button will be shown. If not empty, the first button must be a Pay button.
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_invoice.SendInvoice`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendInvoice

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendInvoice(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            title=title,
            description=description,
            payload=payload,
            currency=currency,
            prices=prices,
            provider_token=provider_token,
            max_tip_amount=max_tip_amount,
            suggested_tip_amounts=suggested_tip_amounts,
            start_parameter=start_parameter,
            provider_data=provider_data,
            photo_url=photo_url,
            photo_size=photo_size,
            photo_width=photo_width,
            photo_height=photo_height,
            need_name=need_name,
            need_phone_number=need_phone_number,
            need_email=need_email,
            need_shipping_address=need_shipping_address,
            send_phone_number_to_provider=send_phone_number_to_provider,
            send_email_to_provider=send_email_to_provider,
            is_flexible=is_flexible,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_invoice(
        self,
        title: str,
        description: str,
        payload: str,
        currency: str,
        prices: list[LabeledPrice],
        provider_token: Optional[str] = None,
        max_tip_amount: Optional[int] = None,
        suggested_tip_amounts: Optional[list[int]] = None,
        start_parameter: Optional[str] = None,
        provider_data: Optional[str] = None,
        photo_url: Optional[str] = None,
        photo_size: Optional[int] = None,
        photo_width: Optional[int] = None,
        photo_height: Optional[int] = None,
        need_name: Optional[bool] = None,
        need_phone_number: Optional[bool] = None,
        need_email: Optional[bool] = None,
        need_shipping_address: Optional[bool] = None,
        send_phone_number_to_provider: Optional[bool] = None,
        send_email_to_provider: Optional[bool] = None,
        is_flexible: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendInvoice:
        """
        Shortcut for method :class:`aiogram.methods.send_invoice.SendInvoice`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send invoices. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendinvoice

        :param title: Product name, 1-32 characters
        :param description: Product description, 1-255 characters
        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use it for your internal processes.
        :param currency: Three-letter ISO 4217 currency code, see `more on currencies <https://core.telegram.org/bots/payments#supported-currencies>`_. Pass 'XTR' for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param prices: Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.). Must contain exactly one item for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param provider_token: Payment provider token, obtained via `@BotFather <https://t.me/botfather>`_. Pass an empty string for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param max_tip_amount: The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of :code:`US$ 1.45` pass :code:`max_tip_amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0. Not supported for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*.
        :param start_parameter: Unique deep-linking parameter. If left empty, **forwarded copies** of the sent message will have a *Pay* button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a *URL* button with a deep link to the bot (instead of a *Pay* button), with the value used as the start parameter
        :param provider_data: JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.
        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.
        :param photo_size: Photo size in bytes
        :param photo_width: Photo width
        :param photo_height: Photo height
        :param need_name: Pass :code:`True` if you require the user's full name to complete the order. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param need_phone_number: Pass :code:`True` if you require the user's phone number to complete the order. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param need_email: Pass :code:`True` if you require the user's email address to complete the order. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param need_shipping_address: Pass :code:`True` if you require the user's shipping address to complete the order. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param send_phone_number_to_provider: Pass :code:`True` if the user's phone number should be sent to the provider. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param send_email_to_provider: Pass :code:`True` if the user's email address should be sent to the provider. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param is_flexible: Pass :code:`True` if the final price depends on the shipping method. Ignored for payments in `Telegram Stars <https://t.me/BotNews/90>`_.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_. If empty, one 'Pay :code:`total price`' button will be shown. If not empty, the first button must be a Pay button.
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_invoice.SendInvoice`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendInvoice

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendInvoice(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            title=title,
            description=description,
            payload=payload,
            currency=currency,
            prices=prices,
            provider_token=provider_token,
            max_tip_amount=max_tip_amount,
            suggested_tip_amounts=suggested_tip_amounts,
            start_parameter=start_parameter,
            provider_data=provider_data,
            photo_url=photo_url,
            photo_size=photo_size,
            photo_width=photo_width,
            photo_height=photo_height,
            need_name=need_name,
            need_phone_number=need_phone_number,
            need_email=need_email,
            need_shipping_address=need_shipping_address,
            send_phone_number_to_provider=send_phone_number_to_provider,
            send_email_to_provider=send_email_to_provider,
            is_flexible=is_flexible,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_location(
        self,
        latitude: float,
        longitude: float,
        horizontal_accuracy: Optional[float] = None,
        live_period: Optional[int] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendLocation:
        """
        Shortcut for method :class:`aiogram.methods.send_location.SendLocation`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send point on the map. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendlocation

        :param latitude: Latitude of the location
        :param longitude: Longitude of the location
        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500
        :param live_period: Period in seconds during which the location will be updated (see `Live Locations <https://telegram.org/blog/live-locations>`_, should be between 60 and 86400, or 0x7FFFFFFF for live locations that can be edited indefinitely.
        :param heading: For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        :param proximity_alert_radius: For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_location.SendLocation`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendLocation

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendLocation(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            latitude=latitude,
            longitude=longitude,
            horizontal_accuracy=horizontal_accuracy,
            live_period=live_period,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_location(
        self,
        latitude: float,
        longitude: float,
        horizontal_accuracy: Optional[float] = None,
        live_period: Optional[int] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendLocation:
        """
        Shortcut for method :class:`aiogram.methods.send_location.SendLocation`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send point on the map. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendlocation

        :param latitude: Latitude of the location
        :param longitude: Longitude of the location
        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500
        :param live_period: Period in seconds during which the location will be updated (see `Live Locations <https://telegram.org/blog/live-locations>`_, should be between 60 and 86400, or 0x7FFFFFFF for live locations that can be edited indefinitely.
        :param heading: For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        :param proximity_alert_radius: For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_location.SendLocation`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendLocation

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendLocation(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            latitude=latitude,
            longitude=longitude,
            horizontal_accuracy=horizontal_accuracy,
            live_period=live_period,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_media_group(
        self,
        media: list[Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]],
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendMediaGroup:
        """
        Shortcut for method :class:`aiogram.methods.send_media_group.SendMediaGroup`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of `Messages <https://core.telegram.org/bots/api#message>`_ that were sent is returned.

        Source: https://core.telegram.org/bots/api#sendmediagroup

        :param media: A JSON-serialized array describing messages to be sent, must include 2-10 items
        :param disable_notification: Sends messages `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent messages from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_media_group.SendMediaGroup`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendMediaGroup

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendMediaGroup(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            media=media,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_media_group(
        self,
        media: list[Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]],
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendMediaGroup:
        """
        Shortcut for method :class:`aiogram.methods.send_media_group.SendMediaGroup`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of `Messages <https://core.telegram.org/bots/api#message>`_ that were sent is returned.

        Source: https://core.telegram.org/bots/api#sendmediagroup

        :param media: A JSON-serialized array describing messages to be sent, must include 2-10 items
        :param disable_notification: Sends messages `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent messages from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the messages are a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_media_group.SendMediaGroup`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendMediaGroup

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendMediaGroup(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            media=media,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply(
        self,
        text: str,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        entities: Optional[list[MessageEntity]] = None,
        link_preview_options: Optional[Union[LinkPreviewOptions, Default]] = Default(
            "link_preview"
        ),
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        disable_web_page_preview: Optional[Union[bool, Default]] = Default(
            "link_preview_is_disabled"
        ),
        **kwargs: Any,
    ) -> SendMessage:
        """
        Shortcut for method :class:`aiogram.methods.send_message.SendMessage`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send text messages. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendmessage

        :param text: Text of the message to be sent, 1-4096 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param entities: A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*
        :param link_preview_options: Link preview generation options for the message
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param disable_web_page_preview: Disables link previews for links in this message
        :return: instance of method :class:`aiogram.methods.send_message.SendMessage`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendMessage

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendMessage(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            link_preview_options=link_preview_options,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            disable_web_page_preview=disable_web_page_preview,
            **kwargs,
        ).as_(self._bot)

    def answer(
        self,
        text: str,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        entities: Optional[list[MessageEntity]] = None,
        link_preview_options: Optional[Union[LinkPreviewOptions, Default]] = Default(
            "link_preview"
        ),
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        disable_web_page_preview: Optional[Union[bool, Default]] = Default(
            "link_preview_is_disabled"
        ),
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendMessage:
        """
        Shortcut for method :class:`aiogram.methods.send_message.SendMessage`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send text messages. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendmessage

        :param text: Text of the message to be sent, 1-4096 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param entities: A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*
        :param link_preview_options: Link preview generation options for the message
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param disable_web_page_preview: Disables link previews for links in this message
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_message.SendMessage`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendMessage

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendMessage(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            link_preview_options=link_preview_options,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            disable_web_page_preview=disable_web_page_preview,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_photo(
        self,
        photo: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        show_caption_above_media: Optional[Union[bool, Default]] = Default(
            "show_caption_above_media"
        ),
        has_spoiler: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendPhoto:
        """
        Shortcut for method :class:`aiogram.methods.send_photo.SendPhoto`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send photos. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendphoto

        :param photo: Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data. The photo must be at most 10 MB in size. The photo's width and height must not exceed 10000 in total. Width and height ratio must be at most 20. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Photo caption (may also be used when resending photos by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the photo caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True`, if the caption must be shown above the message media
        :param has_spoiler: Pass :code:`True` if the photo needs to be covered with a spoiler animation
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_photo.SendPhoto`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendPhoto

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendPhoto(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            has_spoiler=has_spoiler,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_photo(
        self,
        photo: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        show_caption_above_media: Optional[Union[bool, Default]] = Default(
            "show_caption_above_media"
        ),
        has_spoiler: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendPhoto:
        """
        Shortcut for method :class:`aiogram.methods.send_photo.SendPhoto`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send photos. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendphoto

        :param photo: Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data. The photo must be at most 10 MB in size. The photo's width and height must not exceed 10000 in total. Width and height ratio must be at most 20. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Photo caption (may also be used when resending photos by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the photo caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True`, if the caption must be shown above the message media
        :param has_spoiler: Pass :code:`True` if the photo needs to be covered with a spoiler animation
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_photo.SendPhoto`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendPhoto

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendPhoto(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            has_spoiler=has_spoiler,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_poll(
        self,
        question: str,
        options: list[Union[InputPollOption, str]],
        question_parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        question_entities: Optional[list[MessageEntity]] = None,
        is_anonymous: Optional[bool] = None,
        type: Optional[str] = None,
        allows_multiple_answers: Optional[bool] = None,
        correct_option_id: Optional[int] = None,
        explanation: Optional[str] = None,
        explanation_parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        explanation_entities: Optional[list[MessageEntity]] = None,
        open_period: Optional[int] = None,
        close_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        is_closed: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendPoll:
        """
        Shortcut for method :class:`aiogram.methods.send_poll.SendPoll`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send a native poll. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendpoll

        :param question: Poll question, 1-300 characters
        :param options: A JSON-serialized list of 2-10 answer options
        :param question_parse_mode: Mode for parsing entities in the question. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details. Currently, only custom emoji entities are allowed
        :param question_entities: A JSON-serialized list of special entities that appear in the poll question. It can be specified instead of *question_parse_mode*
        :param is_anonymous: :code:`True`, if the poll needs to be anonymous, defaults to :code:`True`
        :param type: Poll type, 'quiz' or 'regular', defaults to 'regular'
        :param allows_multiple_answers: :code:`True`, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to :code:`False`
        :param correct_option_id: 0-based identifier of the correct answer option, required for polls in quiz mode
        :param explanation: Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing
        :param explanation_parse_mode: Mode for parsing entities in the explanation. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param explanation_entities: A JSON-serialized list of special entities that appear in the poll explanation. It can be specified instead of *explanation_parse_mode*
        :param open_period: Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with *close_date*.
        :param close_date: Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with *open_period*.
        :param is_closed: Pass :code:`True` if the poll needs to be immediately closed. This can be useful for poll preview.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_poll.SendPoll`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendPoll

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendPoll(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            question=question,
            options=options,
            question_parse_mode=question_parse_mode,
            question_entities=question_entities,
            is_anonymous=is_anonymous,
            type=type,
            allows_multiple_answers=allows_multiple_answers,
            correct_option_id=correct_option_id,
            explanation=explanation,
            explanation_parse_mode=explanation_parse_mode,
            explanation_entities=explanation_entities,
            open_period=open_period,
            close_date=close_date,
            is_closed=is_closed,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_poll(
        self,
        question: str,
        options: list[Union[InputPollOption, str]],
        question_parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        question_entities: Optional[list[MessageEntity]] = None,
        is_anonymous: Optional[bool] = None,
        type: Optional[str] = None,
        allows_multiple_answers: Optional[bool] = None,
        correct_option_id: Optional[int] = None,
        explanation: Optional[str] = None,
        explanation_parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        explanation_entities: Optional[list[MessageEntity]] = None,
        open_period: Optional[int] = None,
        close_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        is_closed: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendPoll:
        """
        Shortcut for method :class:`aiogram.methods.send_poll.SendPoll`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send a native poll. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendpoll

        :param question: Poll question, 1-300 characters
        :param options: A JSON-serialized list of 2-10 answer options
        :param question_parse_mode: Mode for parsing entities in the question. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details. Currently, only custom emoji entities are allowed
        :param question_entities: A JSON-serialized list of special entities that appear in the poll question. It can be specified instead of *question_parse_mode*
        :param is_anonymous: :code:`True`, if the poll needs to be anonymous, defaults to :code:`True`
        :param type: Poll type, 'quiz' or 'regular', defaults to 'regular'
        :param allows_multiple_answers: :code:`True`, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to :code:`False`
        :param correct_option_id: 0-based identifier of the correct answer option, required for polls in quiz mode
        :param explanation: Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing
        :param explanation_parse_mode: Mode for parsing entities in the explanation. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param explanation_entities: A JSON-serialized list of special entities that appear in the poll explanation. It can be specified instead of *explanation_parse_mode*
        :param open_period: Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with *close_date*.
        :param close_date: Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with *open_period*.
        :param is_closed: Pass :code:`True` if the poll needs to be immediately closed. This can be useful for poll preview.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_poll.SendPoll`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendPoll

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendPoll(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            question=question,
            options=options,
            question_parse_mode=question_parse_mode,
            question_entities=question_entities,
            is_anonymous=is_anonymous,
            type=type,
            allows_multiple_answers=allows_multiple_answers,
            correct_option_id=correct_option_id,
            explanation=explanation,
            explanation_parse_mode=explanation_parse_mode,
            explanation_entities=explanation_entities,
            open_period=open_period,
            close_date=close_date,
            is_closed=is_closed,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_dice(
        self,
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendDice:
        """
        Shortcut for method :class:`aiogram.methods.send_dice.SendDice`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send an animated emoji that will display a random value. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#senddice

        :param emoji: Emoji on which the dice throw animation is based. Currently, must be one of '🎲', '🎯', '🏀', '⚽', '🎳', or '🎰'. Dice can have values 1-6 for '🎲', '🎯' and '🎳', values 1-5 for '🏀' and '⚽', and values 1-64 for '🎰'. Defaults to '🎲'
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_dice.SendDice`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendDice

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendDice(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            emoji=emoji,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_dice(
        self,
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendDice:
        """
        Shortcut for method :class:`aiogram.methods.send_dice.SendDice`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send an animated emoji that will display a random value. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#senddice

        :param emoji: Emoji on which the dice throw animation is based. Currently, must be one of '🎲', '🎯', '🏀', '⚽', '🎳', or '🎰'. Dice can have values 1-6 for '🎲', '🎯' and '🎳', values 1-5 for '🏀' and '⚽', and values 1-64 for '🎰'. Defaults to '🎲'
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_dice.SendDice`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendDice

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendDice(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            emoji=emoji,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_sticker(
        self,
        sticker: Union[InputFile, str],
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendSticker:
        """
        Shortcut for method :class:`aiogram.methods.send_sticker.SendSticker`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send static .WEBP, `animated <https://telegram.org/blog/animated-stickers>`_ .TGS, or `video <https://telegram.org/blog/video-stickers-better-reactions>`_ .WEBM stickers. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendsticker

        :param sticker: Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a .WEBP sticker from the Internet, or upload a new .WEBP, .TGS, or .WEBM sticker using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`. Video and animated stickers can't be sent via an HTTP URL.
        :param emoji: Emoji associated with the sticker; only for just uploaded stickers
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_sticker.SendSticker`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendSticker

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendSticker(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            sticker=sticker,
            emoji=emoji,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_sticker(
        self,
        sticker: Union[InputFile, str],
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendSticker:
        """
        Shortcut for method :class:`aiogram.methods.send_sticker.SendSticker`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send static .WEBP, `animated <https://telegram.org/blog/animated-stickers>`_ .TGS, or `video <https://telegram.org/blog/video-stickers-better-reactions>`_ .WEBM stickers. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendsticker

        :param sticker: Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a .WEBP sticker from the Internet, or upload a new .WEBP, .TGS, or .WEBM sticker using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`. Video and animated stickers can't be sent via an HTTP URL.
        :param emoji: Emoji associated with the sticker; only for just uploaded stickers
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_sticker.SendSticker`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendSticker

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendSticker(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            sticker=sticker,
            emoji=emoji,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_venue(
        self,
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        foursquare_id: Optional[str] = None,
        foursquare_type: Optional[str] = None,
        google_place_id: Optional[str] = None,
        google_place_type: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendVenue:
        """
        Shortcut for method :class:`aiogram.methods.send_venue.SendVenue`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send information about a venue. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendvenue

        :param latitude: Latitude of the venue
        :param longitude: Longitude of the venue
        :param title: Name of the venue
        :param address: Address of the venue
        :param foursquare_id: Foursquare identifier of the venue
        :param foursquare_type: Foursquare type of the venue, if known. (For example, 'arts_entertainment/default', 'arts_entertainment/aquarium' or 'food/icecream'.)
        :param google_place_id: Google Places identifier of the venue
        :param google_place_type: Google Places type of the venue. (See `supported types <https://developers.google.com/places/web-service/supported_types>`_.)
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_venue.SendVenue`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendVenue

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendVenue(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            latitude=latitude,
            longitude=longitude,
            title=title,
            address=address,
            foursquare_id=foursquare_id,
            foursquare_type=foursquare_type,
            google_place_id=google_place_id,
            google_place_type=google_place_type,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_venue(
        self,
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        foursquare_id: Optional[str] = None,
        foursquare_type: Optional[str] = None,
        google_place_id: Optional[str] = None,
        google_place_type: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendVenue:
        """
        Shortcut for method :class:`aiogram.methods.send_venue.SendVenue`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send information about a venue. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendvenue

        :param latitude: Latitude of the venue
        :param longitude: Longitude of the venue
        :param title: Name of the venue
        :param address: Address of the venue
        :param foursquare_id: Foursquare identifier of the venue
        :param foursquare_type: Foursquare type of the venue, if known. (For example, 'arts_entertainment/default', 'arts_entertainment/aquarium' or 'food/icecream'.)
        :param google_place_id: Google Places identifier of the venue
        :param google_place_type: Google Places type of the venue. (See `supported types <https://developers.google.com/places/web-service/supported_types>`_.)
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_venue.SendVenue`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendVenue

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendVenue(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            latitude=latitude,
            longitude=longitude,
            title=title,
            address=address,
            foursquare_id=foursquare_id,
            foursquare_type=foursquare_type,
            google_place_id=google_place_id,
            google_place_type=google_place_type,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_video(
        self,
        video: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumbnail: Optional[InputFile] = None,
        cover: Optional[Union[InputFile, str]] = None,
        start_timestamp: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        show_caption_above_media: Optional[Union[bool, Default]] = Default(
            "show_caption_above_media"
        ),
        has_spoiler: Optional[bool] = None,
        supports_streaming: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendVideo:
        """
        Shortcut for method :class:`aiogram.methods.send_video.SendVideo`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send video files, Telegram clients support MPEG4 videos (other formats may be sent as :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvideo

        :param video: Video to send. Pass a file_id as String to send a video that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a video from the Internet, or upload a new video using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param duration: Duration of sent video in seconds
        :param width: Video width
        :param height: Video height
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param cover: Cover for the video in the message. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More information on Sending Files » <sending-files>`
        :param start_timestamp: Start timestamp for the video in the message
        :param caption: Video caption (may also be used when resending videos by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the video caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True`, if the caption must be shown above the message media
        :param has_spoiler: Pass :code:`True` if the video needs to be covered with a spoiler animation
        :param supports_streaming: Pass :code:`True` if the uploaded video is suitable for streaming
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_video.SendVideo`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendVideo

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendVideo(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            video=video,
            duration=duration,
            width=width,
            height=height,
            thumbnail=thumbnail,
            cover=cover,
            start_timestamp=start_timestamp,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            has_spoiler=has_spoiler,
            supports_streaming=supports_streaming,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_video(
        self,
        video: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumbnail: Optional[InputFile] = None,
        cover: Optional[Union[InputFile, str]] = None,
        start_timestamp: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        show_caption_above_media: Optional[Union[bool, Default]] = Default(
            "show_caption_above_media"
        ),
        has_spoiler: Optional[bool] = None,
        supports_streaming: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendVideo:
        """
        Shortcut for method :class:`aiogram.methods.send_video.SendVideo`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send video files, Telegram clients support MPEG4 videos (other formats may be sent as :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvideo

        :param video: Video to send. Pass a file_id as String to send a video that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a video from the Internet, or upload a new video using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param duration: Duration of sent video in seconds
        :param width: Video width
        :param height: Video height
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param cover: Cover for the video in the message. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass 'attach://<file_attach_name>' to upload a new one using multipart/form-data under <file_attach_name> name. :ref:`More information on Sending Files » <sending-files>`
        :param start_timestamp: Start timestamp for the video in the message
        :param caption: Video caption (may also be used when resending videos by *file_id*), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the video caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True`, if the caption must be shown above the message media
        :param has_spoiler: Pass :code:`True` if the video needs to be covered with a spoiler animation
        :param supports_streaming: Pass :code:`True` if the uploaded video is suitable for streaming
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_video.SendVideo`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendVideo

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendVideo(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            video=video,
            duration=duration,
            width=width,
            height=height,
            thumbnail=thumbnail,
            cover=cover,
            start_timestamp=start_timestamp,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            has_spoiler=has_spoiler,
            supports_streaming=supports_streaming,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_video_note(
        self,
        video_note: Union[InputFile, str],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        thumbnail: Optional[InputFile] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendVideoNote:
        """
        Shortcut for method :class:`aiogram.methods.send_video_note.SendVideoNote`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        As of `v.4.0 <https://telegram.org/blog/video-messages-and-telescope>`_, Telegram clients support rounded square MPEG4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendvideonote

        :param video_note: Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended) or upload a new video using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`. Sending video notes by a URL is currently unsupported
        :param duration: Duration of sent video in seconds
        :param length: Video width and height, i.e. diameter of the video message
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_video_note.SendVideoNote`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendVideoNote

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendVideoNote(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            video_note=video_note,
            duration=duration,
            length=length,
            thumbnail=thumbnail,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_video_note(
        self,
        video_note: Union[InputFile, str],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        thumbnail: Optional[InputFile] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendVideoNote:
        """
        Shortcut for method :class:`aiogram.methods.send_video_note.SendVideoNote`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        As of `v.4.0 <https://telegram.org/blog/video-messages-and-telescope>`_, Telegram clients support rounded square MPEG4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendvideonote

        :param video_note: Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended) or upload a new video using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`. Sending video notes by a URL is currently unsupported
        :param duration: Duration of sent video in seconds
        :param length: Video width and height, i.e. diameter of the video message
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. :ref:`More information on Sending Files » <sending-files>`
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_video_note.SendVideoNote`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendVideoNote

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendVideoNote(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            video_note=video_note,
            duration=duration,
            length=length,
            thumbnail=thumbnail,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def reply_voice(
        self,
        voice: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        duration: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendVoice:
        """
        Shortcut for method :class:`aiogram.methods.send_voice.SendVoice`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS, or in .MP3 format, or in .M4A format (other formats may be sent as :class:`aiogram.types.audio.Audio` or :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvoice

        :param voice: Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Voice message caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the voice message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param duration: Duration of the voice message in seconds
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :return: instance of method :class:`aiogram.methods.send_voice.SendVoice`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendVoice

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendVoice(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            voice=voice,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            **kwargs,
        ).as_(self._bot)

    def answer_voice(
        self,
        voice: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        duration: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        message_effect_id: Optional[str] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> SendVoice:
        """
        Shortcut for method :class:`aiogram.methods.send_voice.SendVoice`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS, or in .MP3 format, or in .M4A format (other formats may be sent as :class:`aiogram.types.audio.Audio` or :class:`aiogram.types.document.Document`). On success, the sent :class:`aiogram.types.message.Message` is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvoice

        :param voice: Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More information on Sending Files » <sending-files>`
        :param caption: Voice message caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the voice message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param duration: Duration of the voice message in seconds
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.send_voice.SendVoice`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendVoice

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendVoice(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            voice=voice,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            message_effect_id=message_effect_id,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def send_copy(  # noqa: C901
        self: Message,
        chat_id: Union[str, int],
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None,
        allow_sending_without_reply: Optional[bool] = None,
        message_thread_id: Optional[int] = None,
        business_connection_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        message_effect_id: Optional[str] = None,
    ) -> Union[
        ForwardMessage,
        SendAnimation,
        SendAudio,
        SendContact,
        SendDocument,
        SendLocation,
        SendMessage,
        SendPhoto,
        SendPoll,
        SendDice,
        SendSticker,
        SendVenue,
        SendVideo,
        SendVideoNote,
        SendVoice,
    ]:
        """
        Send copy of a message.

        Is similar to :meth:`aiogram.client.bot.Bot.copy_message`
        but returning the sent message instead of :class:`aiogram.types.message_id.MessageId`

        .. note::

            This method doesn't use the API method named `copyMessage` and
            historically implemented before the similar method is added to API

        :param chat_id:
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_parameters:
        :param reply_markup:
        :param allow_sending_without_reply:
        :param message_thread_id:
        :param business_connection_id:
        :param parse_mode:
        :param message_effect_id:
        :return:
        """
        from ..methods import (
            ForwardMessage,
            SendAnimation,
            SendAudio,
            SendContact,
            SendDice,
            SendDocument,
            SendLocation,
            SendMessage,
            SendPhoto,
            SendPoll,
            SendSticker,
            SendVenue,
            SendVideo,
            SendVideoNote,
            SendVoice,
        )

        kwargs: Dict[str, Any] = {
            "chat_id": chat_id,
            "reply_markup": reply_markup or self.reply_markup,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "reply_parameters": reply_parameters,
            "message_thread_id": message_thread_id,
            "business_connection_id": business_connection_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            # when sending a copy, we don't need any parse mode
            # because all entities are already prepared
            "parse_mode": parse_mode,
            "message_effect_id": message_effect_id or self.effect_id,
        }

        if self.text:
            return SendMessage(
                text=self.text,
                entities=self.entities,
                **kwargs,
            ).as_(self._bot)
        if self.audio:
            return SendAudio(
                audio=self.audio.file_id,
                caption=self.caption,
                title=self.audio.title,
                performer=self.audio.performer,
                duration=self.audio.duration,
                caption_entities=self.caption_entities,
                **kwargs,
            ).as_(self._bot)
        if self.animation:
            return SendAnimation(
                animation=self.animation.file_id,
                caption=self.caption,
                caption_entities=self.caption_entities,
                **kwargs,
            ).as_(self._bot)
        if self.document:
            return SendDocument(
                document=self.document.file_id,
                caption=self.caption,
                caption_entities=self.caption_entities,
                **kwargs,
            ).as_(self._bot)
        if self.photo:
            return SendPhoto(
                photo=self.photo[-1].file_id,
                caption=self.caption,
                caption_entities=self.caption_entities,
                **kwargs,
            ).as_(self._bot)
        if self.sticker:
            return SendSticker(
                sticker=self.sticker.file_id,
                **kwargs,
            ).as_(self._bot)
        if self.video:
            return SendVideo(
                video=self.video.file_id,
                caption=self.caption,
                caption_entities=self.caption_entities,
                **kwargs,
            ).as_(self._bot)
        if self.video_note:
            return SendVideoNote(
                video_note=self.video_note.file_id,
                **kwargs,
            ).as_(self._bot)
        if self.voice:
            return SendVoice(
                voice=self.voice.file_id,
                **kwargs,
            ).as_(self._bot)
        if self.contact:
            return SendContact(
                phone_number=self.contact.phone_number,
                first_name=self.contact.first_name,
                last_name=self.contact.last_name,
                vcard=self.contact.vcard,
                **kwargs,
            ).as_(self._bot)
        if self.venue:
            return SendVenue(
                latitude=self.venue.location.latitude,
                longitude=self.venue.location.longitude,
                title=self.venue.title,
                address=self.venue.address,
                foursquare_id=self.venue.foursquare_id,
                foursquare_type=self.venue.foursquare_type,
                **kwargs,
            ).as_(self._bot)
        if self.location:
            return SendLocation(
                latitude=self.location.latitude,
                longitude=self.location.longitude,
                **kwargs,
            ).as_(self._bot)
        if self.poll:
            from .input_poll_option import InputPollOption

            return SendPoll(
                question=self.poll.question,
                options=[
                    InputPollOption(
                        text=option.text,
                        voter_count=option.voter_count,
                        text_entities=option.text_entities,
                        text_parse_mode=None,
                    )
                    for option in self.poll.options
                ],
                **kwargs,
            ).as_(self._bot)
        if self.dice:  # Dice value can't be controlled
            return SendDice(
                **kwargs,
            ).as_(self._bot)
        if self.story:
            return ForwardMessage(
                from_chat_id=self.chat.id,
                message_id=self.message_id,
                **kwargs,
            ).as_(self._bot)

        raise TypeError("This type of message can't be copied.")

    def copy_to(
        self,
        chat_id: Union[int, str],
        message_thread_id: Optional[int] = None,
        video_start_timestamp: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        show_caption_above_media: Optional[Union[bool, Default]] = Default(
            "show_caption_above_media"
        ),
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        allow_paid_broadcast: Optional[bool] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        **kwargs: Any,
    ) -> CopyMessage:
        """
        Shortcut for method :class:`aiogram.methods.copy_message.CopyMessage`
        will automatically fill method attributes:

        - :code:`from_chat_id`
        - :code:`message_id`

        Use this method to copy messages of any kind. Service messages, paid media messages, giveaway messages, giveaway winners messages, and invoice messages can't be copied. A quiz :class:`aiogram.methods.poll.Poll` can be copied only if the value of the field *correct_option_id* is known to the bot. The method is analogous to the method :class:`aiogram.methods.forward_message.ForwardMessage`, but the copied message doesn't have a link to the original message. Returns the :class:`aiogram.types.message_id.MessageId` of the sent message on success.

        Source: https://core.telegram.org/bots/api#copymessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param video_start_timestamp: New start timestamp for the copied video in the message
        :param caption: New caption for media, 0-1024 characters after entities parsing. If not specified, the original caption is kept
        :param parse_mode: Mode for parsing entities in the new caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the new caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True`, if the caption must be shown above the message media. Ignored if a new caption isn't specified.
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :return: instance of method :class:`aiogram.methods.copy_message.CopyMessage`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import CopyMessage

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return CopyMessage(
            from_chat_id=self.chat.id,
            message_id=self.message_id,
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            video_start_timestamp=video_start_timestamp,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_to_message_id=reply_to_message_id,
            **kwargs,
        ).as_(self._bot)

    def edit_text(
        self,
        text: str,
        inline_message_id: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        entities: Optional[list[MessageEntity]] = None,
        link_preview_options: Optional[Union[LinkPreviewOptions, Default]] = Default(
            "link_preview"
        ),
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        disable_web_page_preview: Optional[Union[bool, Default]] = Default(
            "link_preview_is_disabled"
        ),
        **kwargs: Any,
    ) -> EditMessageText:
        """
        Shortcut for method :class:`aiogram.methods.edit_message_text.EditMessageText`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`

        Use this method to edit text and `game <https://core.telegram.org/bots/api#games>`_ messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within **48 hours** from the time they were sent.

        Source: https://core.telegram.org/bots/api#editmessagetext

        :param text: New text of the message, 1-4096 characters after entities parsing
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param parse_mode: Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param entities: A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*
        :param link_preview_options: Link preview generation options for the message
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :param disable_web_page_preview: Disables link previews for links in this message
        :return: instance of method :class:`aiogram.methods.edit_message_text.EditMessageText`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditMessageText

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return EditMessageText(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            text=text,
            inline_message_id=inline_message_id,
            parse_mode=parse_mode,
            entities=entities,
            link_preview_options=link_preview_options,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
            **kwargs,
        ).as_(self._bot)

    def forward(
        self,
        chat_id: Union[int, str],
        message_thread_id: Optional[int] = None,
        video_start_timestamp: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[Union[bool, Default]] = Default("protect_content"),
        **kwargs: Any,
    ) -> ForwardMessage:
        """
        Shortcut for method :class:`aiogram.methods.forward_message.ForwardMessage`
        will automatically fill method attributes:

        - :code:`from_chat_id`
        - :code:`message_id`

        Use this method to forward messages of any kind. Service messages and messages with protected content can't be forwarded. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#forwardmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)
        :param message_thread_id: Unique identifier for the target message thread (topic) of the forum; for forum supergroups only
        :param video_start_timestamp: New start timestamp for the forwarded video in the message
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the forwarded message from forwarding and saving
        :return: instance of method :class:`aiogram.methods.forward_message.ForwardMessage`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import ForwardMessage

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return ForwardMessage(
            from_chat_id=self.chat.id,
            message_id=self.message_id,
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            video_start_timestamp=video_start_timestamp,
            disable_notification=disable_notification,
            protect_content=protect_content,
            **kwargs,
        ).as_(self._bot)

    def edit_media(
        self,
        media: InputMediaUnion,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> EditMessageMedia:
        """
        Shortcut for method :class:`aiogram.methods.edit_message_media.EditMessageMedia`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`

        Use this method to edit animation, audio, document, photo, or video messages, or to add media to text messages. If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo or a video otherwise. When an inline message is edited, a new file can't be uploaded; use a previously uploaded file via its file_id or specify a URL. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within **48 hours** from the time they were sent.

        Source: https://core.telegram.org/bots/api#editmessagemedia

        :param media: A JSON-serialized object for a new media content of the message
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param reply_markup: A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :return: instance of method :class:`aiogram.methods.edit_message_media.EditMessageMedia`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditMessageMedia

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return EditMessageMedia(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            media=media,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
            **kwargs,
        ).as_(self._bot)

    def edit_reply_markup(
        self,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> EditMessageReplyMarkup:
        """
        Shortcut for method :class:`aiogram.methods.edit_message_reply_markup.EditMessageReplyMarkup`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`

        Use this method to edit only the reply markup of messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within **48 hours** from the time they were sent.

        Source: https://core.telegram.org/bots/api#editmessagereplymarkup

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :return: instance of method :class:`aiogram.methods.edit_message_reply_markup.EditMessageReplyMarkup`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditMessageReplyMarkup

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return EditMessageReplyMarkup(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
            **kwargs,
        ).as_(self._bot)

    def delete_reply_markup(
        self,
        inline_message_id: Optional[str] = None,
        **kwargs: Any,
    ) -> EditMessageReplyMarkup:
        """
        Shortcut for method :class:`aiogram.methods.edit_message_reply_markup.EditMessageReplyMarkup`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`
        - :code:`reply_markup`

        Use this method to edit only the reply markup of messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within **48 hours** from the time they were sent.

        Source: https://core.telegram.org/bots/api#editmessagereplymarkup

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :return: instance of method :class:`aiogram.methods.edit_message_reply_markup.EditMessageReplyMarkup`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditMessageReplyMarkup

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return EditMessageReplyMarkup(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            reply_markup=None,
            inline_message_id=inline_message_id,
            **kwargs,
        ).as_(self._bot)

    def edit_live_location(
        self,
        latitude: float,
        longitude: float,
        inline_message_id: Optional[str] = None,
        live_period: Optional[int] = None,
        horizontal_accuracy: Optional[float] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> EditMessageLiveLocation:
        """
        Shortcut for method :class:`aiogram.methods.edit_message_live_location.EditMessageLiveLocation`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`

        Use this method to edit live location messages. A location can be edited until its *live_period* expires or editing is explicitly disabled by a call to :class:`aiogram.methods.stop_message_live_location.StopMessageLiveLocation`. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#editmessagelivelocation

        :param latitude: Latitude of new location
        :param longitude: Longitude of new location
        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param live_period: New period in seconds during which the location can be updated, starting from the message send date. If 0x7FFFFFFF is specified, then the location can be updated forever. Otherwise, the new value must not exceed the current *live_period* by more than a day, and the live location expiration date must remain within the next 90 days. If not specified, then *live_period* remains unchanged
        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500
        :param heading: Direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        :param proximity_alert_radius: The maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        :param reply_markup: A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :return: instance of method :class:`aiogram.methods.edit_message_live_location.EditMessageLiveLocation`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditMessageLiveLocation

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return EditMessageLiveLocation(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            latitude=latitude,
            longitude=longitude,
            inline_message_id=inline_message_id,
            live_period=live_period,
            horizontal_accuracy=horizontal_accuracy,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
            reply_markup=reply_markup,
            **kwargs,
        ).as_(self._bot)

    def stop_live_location(
        self,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> StopMessageLiveLocation:
        """
        Shortcut for method :class:`aiogram.methods.stop_message_live_location.StopMessageLiveLocation`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`

        Use this method to stop updating a live location message before *live_period* expires. On success, if the message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

        Source: https://core.telegram.org/bots/api#stopmessagelivelocation

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param reply_markup: A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :return: instance of method :class:`aiogram.methods.stop_message_live_location.StopMessageLiveLocation`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import StopMessageLiveLocation

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return StopMessageLiveLocation(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            inline_message_id=inline_message_id,
            reply_markup=reply_markup,
            **kwargs,
        ).as_(self._bot)

    def edit_caption(
        self,
        inline_message_id: Optional[str] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
        caption_entities: Optional[list[MessageEntity]] = None,
        show_caption_above_media: Optional[Union[bool, Default]] = Default(
            "show_caption_above_media"
        ),
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> EditMessageCaption:
        """
        Shortcut for method :class:`aiogram.methods.edit_message_caption.EditMessageCaption`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`

        Use this method to edit captions of messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within **48 hours** from the time they were sent.

        Source: https://core.telegram.org/bots/api#editmessagecaption

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message
        :param caption: New caption of the message, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True`, if the caption must be shown above the message media. Supported only for animation, photo and video messages.
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_.
        :return: instance of method :class:`aiogram.methods.edit_message_caption.EditMessageCaption`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import EditMessageCaption

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return EditMessageCaption(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            inline_message_id=inline_message_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            reply_markup=reply_markup,
            **kwargs,
        ).as_(self._bot)

    def delete(
        self,
        **kwargs: Any,
    ) -> DeleteMessage:
        """
        Shortcut for method :class:`aiogram.methods.delete_message.DeleteMessage`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`

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

        :return: instance of method :class:`aiogram.methods.delete_message.DeleteMessage`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import DeleteMessage

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return DeleteMessage(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            **kwargs,
        ).as_(self._bot)

    def pin(
        self,
        disable_notification: Optional[bool] = None,
        **kwargs: Any,
    ) -> PinChatMessage:
        """
        Shortcut for method :class:`aiogram.methods.pin_chat_message.PinChatMessage`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`

        Use this method to add a message to the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#pinchatmessage

        :param disable_notification: Pass :code:`True` if it is not necessary to send a notification to all chat members about the new pinned message. Notifications are always disabled in channels and private chats.
        :return: instance of method :class:`aiogram.methods.pin_chat_message.PinChatMessage`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import PinChatMessage

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return PinChatMessage(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            disable_notification=disable_notification,
            **kwargs,
        ).as_(self._bot)

    def unpin(
        self,
        **kwargs: Any,
    ) -> UnpinChatMessage:
        """
        Shortcut for method :class:`aiogram.methods.unpin_chat_message.UnpinChatMessage`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`

        Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' administrator right in a supergroup or 'can_edit_messages' administrator right in a channel. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#unpinchatmessage

        :return: instance of method :class:`aiogram.methods.unpin_chat_message.UnpinChatMessage`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import UnpinChatMessage

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return UnpinChatMessage(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            **kwargs,
        ).as_(self._bot)

    def get_url(
        self, force_private: bool = False, include_thread_id: bool = False
    ) -> Optional[str]:
        """
        Returns message URL. Cannot be used in private (one-to-one) chats.
        If chat has a username, returns URL like https://t.me/username/message_id
        Otherwise (or if {force_private} flag is set), returns https://t.me/c/shifted_chat_id/message_id

        :param force_private: if set, a private URL is returned even for a public chat
        :param include_thread_id: if set, adds chat thread id to URL and returns like https://t.me/username/thread_id/message_id
        :return: string with full message URL
        """
        if self.chat.type in ("private", "group"):
            return None

        chat_value = (
            f"c/{self.chat.shifted_id}"
            if not self.chat.username or force_private
            else self.chat.username
        )

        message_id_value = (
            f"{self.message_thread_id}/{self.message_id}"
            if include_thread_id and self.message_thread_id and self.is_topic_message
            else f"{self.message_id}"
        )

        return f"https://t.me/{chat_value}/{message_id_value}"

    def react(
        self,
        reaction: Optional[list[ReactionTypeUnion]] = None,
        is_big: Optional[bool] = None,
        **kwargs: Any,
    ) -> SetMessageReaction:
        """
        Shortcut for method :class:`aiogram.methods.set_message_reaction.SetMessageReaction`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_id`
        - :code:`business_connection_id`

        Use this method to change the chosen reactions on a message. Service messages of some types can't be reacted to. Automatically forwarded messages from a channel to its discussion group have the same available reactions as messages in the channel. Bots can't use paid reactions. Returns :code:`True` on success.

        Source: https://core.telegram.org/bots/api#setmessagereaction

        :param reaction: A JSON-serialized list of reaction types to set on the message. Currently, as non-premium users, bots can set up to one reaction per message. A custom emoji reaction can be used if it is either already present on the message or explicitly allowed by chat administrators. Paid reactions can't be used by bots.
        :param is_big: Pass :code:`True` to set the reaction with a big animation
        :return: instance of method :class:`aiogram.methods.set_message_reaction.SetMessageReaction`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SetMessageReaction

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SetMessageReaction(
            chat_id=self.chat.id,
            message_id=self.message_id,
            business_connection_id=self.business_connection_id,
            reaction=reaction,
            is_big=is_big,
            **kwargs,
        ).as_(self._bot)

    def answer_paid_media(
        self,
        star_count: int,
        media: list[InputPaidMediaUnion],
        payload: Optional[str] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[list[MessageEntity]] = None,
        show_caption_above_media: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        allow_paid_broadcast: Optional[bool] = None,
        reply_parameters: Optional[ReplyParameters] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendPaidMedia:
        """
        Shortcut for method :class:`aiogram.methods.send_paid_media.SendPaidMedia`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`

        Use this method to send paid media. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendpaidmedia

        :param star_count: The number of Telegram Stars that must be paid to buy access to the media; 1-2500
        :param media: A JSON-serialized array describing the media to be sent; up to 10 items
        :param payload: Bot-defined paid media payload, 0-128 bytes. This will not be displayed to the user, use it for your internal processes.
        :param caption: Media caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the media caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True`, if the caption must be shown above the message media
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param reply_parameters: Description of the message to reply to
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :return: instance of method :class:`aiogram.methods.send_paid_media.SendPaidMedia`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendPaidMedia

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendPaidMedia(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            star_count=star_count,
            media=media,
            payload=payload,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            reply_parameters=reply_parameters,
            reply_markup=reply_markup,
            **kwargs,
        ).as_(self._bot)

    def reply_paid_media(
        self,
        star_count: int,
        media: list[InputPaidMediaUnion],
        payload: Optional[str] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[list[MessageEntity]] = None,
        show_caption_above_media: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        allow_paid_broadcast: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendPaidMedia:
        """
        Shortcut for method :class:`aiogram.methods.send_paid_media.SendPaidMedia`
        will automatically fill method attributes:

        - :code:`chat_id`
        - :code:`message_thread_id`
        - :code:`business_connection_id`
        - :code:`reply_parameters`

        Use this method to send paid media. On success, the sent :class:`aiogram.types.message.Message` is returned.

        Source: https://core.telegram.org/bots/api#sendpaidmedia

        :param star_count: The number of Telegram Stars that must be paid to buy access to the media; 1-2500
        :param media: A JSON-serialized array describing the media to be sent; up to 10 items
        :param payload: Bot-defined paid media payload, 0-128 bytes. This will not be displayed to the user, use it for your internal processes.
        :param caption: Media caption, 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the media caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details.
        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*
        :param show_caption_above_media: Pass :code:`True`, if the caption must be shown above the message media
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_paid_broadcast: Pass :code:`True` to allow up to 1000 messages per second, ignoring `broadcasting limits <https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once>`_ for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :param reply_markup: Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_, `custom reply keyboard <https://core.telegram.org/bots/features#keyboards>`_, instructions to remove a reply keyboard or to force a reply from the user
        :return: instance of method :class:`aiogram.methods.send_paid_media.SendPaidMedia`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import SendPaidMedia

        assert (
            self.chat is not None
        ), "This method can be used only if chat is present in the message."

        return SendPaidMedia(
            chat_id=self.chat.id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            business_connection_id=self.business_connection_id,
            reply_parameters=self.as_reply_parameters(),
            star_count=star_count,
            media=media,
            payload=payload,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            show_caption_above_media=show_caption_above_media,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_paid_broadcast=allow_paid_broadcast,
            reply_markup=reply_markup,
            **kwargs,
        ).as_(self._bot)
