from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, List, Optional, Union

from pydantic import Field

from aiogram.utils import helper
from aiogram.utils.text_decorations import TextDecoration, html_decoration, markdown_decoration

from .base import UNSET, TelegramObject

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
        SendPhoto,
        SendPoll,
        SendSticker,
        SendVenue,
        SendVideo,
        SendVideoNote,
        SendVoice,
        StopMessageLiveLocation,
        UnpinChatMessage,
    )
    from .animation import Animation
    from .audio import Audio
    from .chat import Chat
    from .contact import Contact
    from .dice import Dice
    from .document import Document
    from .force_reply import ForceReply
    from .forum_topic_closed import ForumTopicClosed
    from .forum_topic_created import ForumTopicCreated
    from .forum_topic_reopened import ForumTopicReopened
    from .game import Game
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .input_file import InputFile
    from .input_media import InputMedia
    from .input_media_audio import InputMediaAudio
    from .input_media_document import InputMediaDocument
    from .input_media_photo import InputMediaPhoto
    from .input_media_video import InputMediaVideo
    from .invoice import Invoice
    from .labeled_price import LabeledPrice
    from .location import Location
    from .message_auto_delete_timer_changed import MessageAutoDeleteTimerChanged
    from .message_entity import MessageEntity
    from .passport_data import PassportData
    from .photo_size import PhotoSize
    from .poll import Poll
    from .proximity_alert_triggered import ProximityAlertTriggered
    from .reply_keyboard_markup import ReplyKeyboardMarkup
    from .reply_keyboard_remove import ReplyKeyboardRemove
    from .sticker import Sticker
    from .successful_payment import SuccessfulPayment
    from .user import User
    from .venue import Venue
    from .video import Video
    from .video_chat_ended import VideoChatEnded
    from .video_chat_participants_invited import VideoChatParticipantsInvited
    from .video_chat_scheduled import VideoChatScheduled
    from .video_chat_started import VideoChatStarted
    from .video_note import VideoNote
    from .voice import Voice
    from .web_app_data import WebAppData


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
    message_thread_id: Optional[int] = None
    """*Optional*. Unique identifier of a message thread to which the message belongs; for supergroups only"""
    from_user: Optional[User] = Field(None, alias="from")
    """*Optional*. Sender of the message; empty for messages sent to channels. For backward compatibility, the field contains a fake sender user in non-channel chats, if the message was sent on behalf of a chat."""
    sender_chat: Optional[Chat] = None
    """*Optional*. Sender of the message, sent on behalf of a chat. For example, the channel itself for channel posts, the supergroup itself for messages from anonymous group administrators, the linked channel for messages automatically forwarded to the discussion group. For backward compatibility, the field *from* contains a fake sender user in non-channel chats, if the message was sent on behalf of a chat."""
    forward_from: Optional[User] = None
    """*Optional*. For forwarded messages, sender of the original message"""
    forward_from_chat: Optional[Chat] = None
    """*Optional*. For messages forwarded from channels or from anonymous administrators, information about the original sender chat"""
    forward_from_message_id: Optional[int] = None
    """*Optional*. For messages forwarded from channels, identifier of the original message in the channel"""
    forward_signature: Optional[str] = None
    """*Optional*. For forwarded messages that were originally sent in channels or by an anonymous chat administrator, signature of the message sender if present"""
    forward_sender_name: Optional[str] = None
    """*Optional*. Sender's name for messages forwarded from users who disallow adding a link to their account in forwarded messages"""
    forward_date: Optional[int] = None
    """*Optional*. For forwarded messages, date the original message was sent in Unix time"""
    is_topic_message: Optional[bool] = None
    """*Optional*. :code:`True`, if the message is sent to a forum topic"""
    is_automatic_forward: Optional[bool] = None
    """*Optional*. :code:`True`, if the message is a channel post that was automatically forwarded to the connected discussion group"""
    reply_to_message: Optional[Message] = None
    """*Optional*. For replies, the original message. Note that the Message object in this field will not contain further *reply_to_message* fields even if it itself is a reply."""
    via_bot: Optional[User] = None
    """*Optional*. Bot through which the message was sent"""
    edit_date: Optional[int] = None
    """*Optional*. Date the message was last edited in Unix time"""
    has_protected_content: Optional[bool] = None
    """*Optional*. :code:`True`, if the message can't be forwarded"""
    media_group_id: Optional[str] = None
    """*Optional*. The unique identifier of a media message group this message belongs to"""
    author_signature: Optional[str] = None
    """*Optional*. Signature of the post author for messages in channels, or the custom title of an anonymous group administrator"""
    text: Optional[str] = None
    """*Optional*. For text messages, the actual UTF-8 text of the message"""
    entities: Optional[List[MessageEntity]] = None
    """*Optional*. For text messages, special entities like usernames, URLs, bot commands, etc. that appear in the text"""
    animation: Optional[Animation] = None
    """*Optional*. Message is an animation, information about the animation. For backward compatibility, when this field is set, the *document* field will also be set"""
    audio: Optional[Audio] = None
    """*Optional*. Message is an audio file, information about the file"""
    document: Optional[Document] = None
    """*Optional*. Message is a general file, information about the file"""
    photo: Optional[List[PhotoSize]] = None
    """*Optional*. Message is a photo, available sizes of the photo"""
    sticker: Optional[Sticker] = None
    """*Optional*. Message is a sticker, information about the sticker"""
    video: Optional[Video] = None
    """*Optional*. Message is a video, information about the video"""
    video_note: Optional[VideoNote] = None
    """*Optional*. Message is a `video note <https://telegram.org/blog/video-messages-and-telescope>`_, information about the video message"""
    voice: Optional[Voice] = None
    """*Optional*. Message is a voice message, information about the file"""
    caption: Optional[str] = None
    """*Optional*. Caption for the animation, audio, document, photo, video or voice"""
    caption_entities: Optional[List[MessageEntity]] = None
    """*Optional*. For messages with a caption, special entities like usernames, URLs, bot commands, etc. that appear in the caption"""
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
    new_chat_members: Optional[List[User]] = None
    """*Optional*. New members that were added to the group or supergroup and information about them (the bot itself may be one of these members)"""
    left_chat_member: Optional[User] = None
    """*Optional*. A member was removed from the group, information about them (this member may be the bot itself)"""
    new_chat_title: Optional[str] = None
    """*Optional*. A chat title was changed to this value"""
    new_chat_photo: Optional[List[PhotoSize]] = None
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
    pinned_message: Optional[Message] = None
    """*Optional*. Specified message was pinned. Note that the Message object in this field will not contain further *reply_to_message* fields even if it is itself a reply."""
    invoice: Optional[Invoice] = None
    """*Optional*. Message is an invoice for a `payment <https://core.telegram.org/bots/api#payments>`_, information about the invoice. `More about payments » <https://core.telegram.org/bots/api#payments>`_"""
    successful_payment: Optional[SuccessfulPayment] = None
    """*Optional*. Message is a service message about a successful payment, information about the payment. `More about payments » <https://core.telegram.org/bots/api#payments>`_"""
    connected_website: Optional[str] = None
    """*Optional*. The domain name of the website on which the user has logged in. `More about Telegram Login » <https://core.telegram.org/widgets/login>`_"""
    passport_data: Optional[PassportData] = None
    """*Optional*. Telegram Passport data"""
    proximity_alert_triggered: Optional[ProximityAlertTriggered] = None
    """*Optional*. Service message. A user in the chat triggered another user's proximity alert while sharing Live Location."""
    forum_topic_created: Optional[ForumTopicCreated] = None
    """*Optional*. Service message: forum topic created"""
    forum_topic_closed: Optional[ForumTopicClosed] = None
    """*Optional*. Service message: forum topic closed"""
    forum_topic_reopened: Optional[ForumTopicReopened] = None
    """*Optional*. Service message: forum topic reopened"""
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
        if self.forum_topic_closed:
            return ContentType.FORUM_TOPIC_CLOSED
        if self.forum_topic_reopened:
            return ContentType.FORUM_TOPIC_REOPENED
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

    def reply_animation(
        self,
        animation: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendAnimation:
        """
        Reply with animation

        :param animation:
        :param duration:
        :param width:
        :param height:
        :param thumb:
        :param caption:
        :param parse_mode:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendAnimation

        return SendAnimation(
            chat_id=self.chat.id,
            animation=animation,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_animation(
        self,
        animation: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendAnimation:
        """
        Answer with animation

        :param animation:
        :param duration:
        :param width:
        :param height:
        :param thumb:
        :param caption:
        :param parse_mode:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendAnimation

        return SendAnimation(
            chat_id=self.chat.id,
            animation=animation,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_audio(
        self,
        audio: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendAudio:
        """
        Reply with audio

        :param audio:
        :param caption:
        :param parse_mode:
        :param duration:
        :param performer:
        :param title:
        :param thumb:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendAudio

        return SendAudio(
            chat_id=self.chat.id,
            audio=audio,
            caption=caption,
            parse_mode=parse_mode,
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_audio(
        self,
        audio: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendAudio:
        """
        Answer with audio

        :param audio:
        :param caption:
        :param parse_mode:
        :param duration:
        :param performer:
        :param title:
        :param thumb:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendAudio

        return SendAudio(
            chat_id=self.chat.id,
            audio=audio,
            caption=caption,
            parse_mode=parse_mode,
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_contact(
        self,
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        vcard: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendContact:
        """
        Reply with contact

        :param phone_number:
        :param first_name:
        :param last_name:
        :param vcard:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendContact

        return SendContact(
            chat_id=self.chat.id,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            vcard=vcard,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_contact(
        self,
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        vcard: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendContact:
        """
        Answer with contact

        :param phone_number:
        :param first_name:
        :param last_name:
        :param vcard:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendContact

        return SendContact(
            chat_id=self.chat.id,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            vcard=vcard,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_document(
        self,
        document: Union[InputFile, str],
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendDocument:
        """
        Reply with document

        :param document:
        :param thumb:
        :param caption:
        :param parse_mode:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendDocument

        return SendDocument(
            chat_id=self.chat.id,
            document=document,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_document(
        self,
        document: Union[InputFile, str],
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendDocument:
        """
        Answer with document

        :param document:
        :param thumb:
        :param caption:
        :param parse_mode:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendDocument

        return SendDocument(
            chat_id=self.chat.id,
            document=document,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_game(
        self,
        game_short_name: str,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> SendGame:
        """
        Reply with game

        :param game_short_name:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendGame

        return SendGame(
            chat_id=self.chat.id,
            game_short_name=game_short_name,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_game(
        self,
        game_short_name: str,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> SendGame:
        """
        Answer with game

        :param game_short_name:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendGame

        return SendGame(
            chat_id=self.chat.id,
            game_short_name=game_short_name,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_invoice(
        self,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        currency: str,
        prices: List[LabeledPrice],
        max_tip_amount: Optional[int] = None,
        suggested_tip_amounts: Optional[List[int]] = None,
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
        protect_content: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> SendInvoice:
        """
        Reply with invoice

        :param title: Product name, 1-32 characters
        :param description: Product description, 1-255 characters
        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.
        :param provider_token: Payment provider token, obtained via `@BotFather <https://t.me/botfather>`_
        :param currency: Three-letter ISO 4217 currency code, see `more on currencies <https://core.telegram.org/bots/payments#supported-currencies>`_
        :param prices: Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :param max_tip_amount: The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of :code:`US$ 1.45` pass :code:`max_tip_amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0
        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*.
        :param start_parameter: Unique deep-linking parameter. If left empty, **forwarded copies** of the sent message will have a *Pay* button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a *URL* button with a deep link to the bot (instead of a *Pay* button), with the value used as the start parameter
        :param provider_data: JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.
        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.
        :param photo_size: Photo size in bytes
        :param photo_width: Photo width
        :param photo_height: Photo height
        :param need_name: Pass :code:`True` if you require the user's full name to complete the order
        :param need_phone_number: Pass :code:`True` if you require the user's phone number to complete the order
        :param need_email: Pass :code:`True` if you require the user's email address to complete the order
        :param need_shipping_address: Pass :code:`True` if you require the user's shipping address to complete the order
        :param send_phone_number_to_provider: Pass :code:`True` if the user's phone number should be sent to provider
        :param send_email_to_provider: Pass :code:`True` if the user's email address should be sent to provider
        :param is_flexible: Pass :code:`True` if the final price depends on the shipping method
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param allow_sending_without_reply: Pass :code:`True` if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_. If empty, one 'Pay :code:`total price`' button will be shown. If not empty, the first button must be a Pay button.
        :return: On success, the sent Message is returned.
        """
        from ..methods import SendInvoice

        return SendInvoice(
            chat_id=self.chat.id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
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
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_invoice(
        self,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        currency: str,
        prices: List[LabeledPrice],
        max_tip_amount: Optional[int] = None,
        suggested_tip_amounts: Optional[List[int]] = None,
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
        protect_content: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> SendInvoice:
        """
        Answer with invoice

        :param title: Product name, 1-32 characters
        :param description: Product description, 1-255 characters
        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.
        :param provider_token: Payment provider token, obtained via `@BotFather <https://t.me/botfather>`_
        :param currency: Three-letter ISO 4217 currency code, see `more on currencies <https://core.telegram.org/bots/payments#supported-currencies>`_
        :param prices: Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :param max_tip_amount: The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of :code:`US$ 1.45` pass :code:`max_tip_amount = 145`. See the *exp* parameter in `currencies.json <https://core.telegram.org/bots/payments/currencies.json>`_, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0
        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*.
        :param start_parameter: Unique deep-linking parameter. If left empty, **forwarded copies** of the sent message will have a *Pay* button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a *URL* button with a deep link to the bot (instead of a *Pay* button), with the value used as the start parameter
        :param provider_data: JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.
        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.
        :param photo_size: Photo size in bytes
        :param photo_width: Photo width
        :param photo_height: Photo height
        :param need_name: Pass :code:`True` if you require the user's full name to complete the order
        :param need_phone_number: Pass :code:`True` if you require the user's phone number to complete the order
        :param need_email: Pass :code:`True` if you require the user's email address to complete the order
        :param need_shipping_address: Pass :code:`True` if you require the user's shipping address to complete the order
        :param send_phone_number_to_provider: Pass :code:`True` if the user's phone number should be sent to provider
        :param send_email_to_provider: Pass :code:`True` if the user's email address should be sent to provider
        :param is_flexible: Pass :code:`True` if the final price depends on the shipping method
        :param disable_notification: Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :param reply_markup: A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_. If empty, one 'Pay :code:`total price`' button will be shown. If not empty, the first button must be a Pay button.
        :return: On success, the sent Message is returned.
        """
        from ..methods import SendInvoice

        return SendInvoice(
            chat_id=self.chat.id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            currency=currency,
            prices=prices,
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
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_location(
        self,
        latitude: float,
        longitude: float,
        live_period: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendLocation:
        """
        Reply with location

        :param latitude:
        :param longitude:
        :param live_period:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendLocation

        return SendLocation(
            chat_id=self.chat.id,
            latitude=latitude,
            longitude=longitude,
            live_period=live_period,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_location(
        self,
        latitude: float,
        longitude: float,
        live_period: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendLocation:
        """
        Answer with location

        :param latitude:
        :param longitude:
        :param live_period:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendLocation

        return SendLocation(
            chat_id=self.chat.id,
            latitude=latitude,
            longitude=longitude,
            live_period=live_period,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_media_group(
        self,
        media: List[Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]],
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendMediaGroup:
        """
        Reply with media group

        :param media:
        :param disable_notification:
        :param allow_sending_without_reply:
        :return:
        """
        from ..methods import SendMediaGroup

        return SendMediaGroup(
            chat_id=self.chat.id,
            media=media,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_media_group(
        self,
        media: List[Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]],
        disable_notification: Optional[bool] = None,
        **kwargs: Any,
    ) -> SendMediaGroup:
        """
        Answer with media group

        :param media:
        :param disable_notification:
        :return:
        """
        from ..methods import SendMediaGroup

        return SendMediaGroup(
            chat_id=self.chat.id,
            media=media,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply(
        self,
        text: str,
        parse_mode: Optional[str] = UNSET,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendMessage:
        """
        Reply with text message

        :param text:
        :param parse_mode:
        :param disable_web_page_preview:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendMessage

        return SendMessage(
            chat_id=self.chat.id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer(
        self,
        text: str,
        parse_mode: Optional[str] = UNSET,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendMessage:
        """
        Answer with text message

        :param text:
        :param parse_mode:
        :param disable_web_page_preview:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendMessage

        return SendMessage(
            chat_id=self.chat.id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_photo(
        self,
        photo: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendPhoto:
        """
        Reply with photo

        :param photo:
        :param caption:
        :param parse_mode:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendPhoto

        return SendPhoto(
            chat_id=self.chat.id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_photo(
        self,
        photo: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendPhoto:
        """
        Answer with photo

        :param photo:
        :param caption:
        :param parse_mode:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendPhoto

        return SendPhoto(
            chat_id=self.chat.id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_poll(
        self,
        question: str,
        options: List[str],
        is_anonymous: Optional[bool] = None,
        type: Optional[str] = None,
        allows_multiple_answers: Optional[bool] = None,
        correct_option_id: Optional[int] = None,
        explanation: Optional[str] = None,
        explanation_parse_mode: Optional[str] = UNSET,
        open_period: Optional[int] = None,
        close_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        is_closed: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendPoll:
        """
        Reply with poll

        :param question:
        :param options:
        :param is_anonymous:
        :param type:
        :param allows_multiple_answers:
        :param correct_option_id:
        :param explanation:
        :param explanation_parse_mode:
        :param open_period:
        :param close_date:
        :param is_closed:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendPoll

        return SendPoll(
            chat_id=self.chat.id,
            question=question,
            options=options,
            is_anonymous=is_anonymous,
            type=type,
            allows_multiple_answers=allows_multiple_answers,
            correct_option_id=correct_option_id,
            explanation=explanation,
            explanation_parse_mode=explanation_parse_mode,
            open_period=open_period,
            close_date=close_date,
            is_closed=is_closed,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_poll(
        self,
        question: str,
        options: List[str],
        is_anonymous: Optional[bool] = None,
        type: Optional[str] = None,
        allows_multiple_answers: Optional[bool] = None,
        correct_option_id: Optional[int] = None,
        explanation: Optional[str] = None,
        explanation_parse_mode: Optional[str] = UNSET,
        open_period: Optional[int] = None,
        close_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None,
        is_closed: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendPoll:
        """
        Answer with poll

        :param question:
        :param options:
        :param is_anonymous:
        :param type:
        :param allows_multiple_answers:
        :param correct_option_id:
                :param explanation:
        :param explanation_parse_mode:
        :param open_period:
        :param close_date:
        :param is_closed:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendPoll

        return SendPoll(
            chat_id=self.chat.id,
            question=question,
            options=options,
            is_anonymous=is_anonymous,
            type=type,
            allows_multiple_answers=allows_multiple_answers,
            correct_option_id=correct_option_id,
            explanation=explanation,
            explanation_parse_mode=explanation_parse_mode,
            open_period=open_period,
            close_date=close_date,
            is_closed=is_closed,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_dice(
        self,
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendDice:
        """
        Reply with dice

        :param emoji:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendDice

        return SendDice(
            chat_id=self.chat.id,
            emoji=emoji,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_dice(
        self,
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendDice:
        """
        Answer with dice

        :param emoji:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendDice

        return SendDice(
            chat_id=self.chat.id,
            emoji=emoji,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_sticker(
        self,
        sticker: Union[InputFile, str],
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendSticker:
        """
        Reply with sticker

        :param sticker:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendSticker

        return SendSticker(
            chat_id=self.chat.id,
            sticker=sticker,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_sticker(
        self,
        sticker: Union[InputFile, str],
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendSticker:
        """
        Answer with sticker

        :param sticker:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendSticker

        return SendSticker(
            chat_id=self.chat.id,
            sticker=sticker,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_venue(
        self,
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        foursquare_id: Optional[str] = None,
        foursquare_type: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendVenue:
        """
        Reply with venue

        :param latitude:
        :param longitude:
        :param title:
        :param address:
        :param foursquare_id:
        :param foursquare_type:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendVenue

        return SendVenue(
            chat_id=self.chat.id,
            latitude=latitude,
            longitude=longitude,
            title=title,
            address=address,
            foursquare_id=foursquare_id,
            foursquare_type=foursquare_type,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_venue(
        self,
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        foursquare_id: Optional[str] = None,
        foursquare_type: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendVenue:
        """
        Answer with venue

        :param latitude:
        :param longitude:
        :param title:
        :param address:
        :param foursquare_id:
        :param foursquare_type:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendVenue

        return SendVenue(
            chat_id=self.chat.id,
            latitude=latitude,
            longitude=longitude,
            title=title,
            address=address,
            foursquare_id=foursquare_id,
            foursquare_type=foursquare_type,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_video(
        self,
        video: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        supports_streaming: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendVideo:
        """
        Reply with video

        :param video:
        :param duration:
        :param width:
        :param height:
        :param thumb:
        :param caption:
        :param parse_mode:
        :param supports_streaming:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendVideo

        return SendVideo(
            chat_id=self.chat.id,
            video=video,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            supports_streaming=supports_streaming,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_video(
        self,
        video: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        supports_streaming: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendVideo:
        """
        Answer with video

        :param video:
        :param duration:
        :param width:
        :param height:
        :param thumb:
        :param caption:
        :param parse_mode:
        :param supports_streaming:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendVideo

        return SendVideo(
            chat_id=self.chat.id,
            video=video,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            supports_streaming=supports_streaming,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_video_note(
        self,
        video_note: Union[InputFile, str],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendVideoNote:
        """
        Reply wit video note

        :param video_note:
        :param duration:
        :param length:
        :param thumb:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendVideoNote

        return SendVideoNote(
            chat_id=self.chat.id,
            video_note=video_note,
            duration=duration,
            length=length,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_video_note(
        self,
        video_note: Union[InputFile, str],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendVideoNote:
        """
        Answer wit video note

        :param video_note:
        :param duration:
        :param length:
        :param thumb:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendVideoNote

        return SendVideoNote(
            chat_id=self.chat.id,
            video_note=video_note,
            duration=duration,
            length=length,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def reply_voice(
        self,
        voice: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        duration: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendVoice:
        """
        Reply with voice

        :param voice:
        :param caption:
        :param parse_mode:
        :param duration:
        :param disable_notification:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import SendVoice

        return SendVoice(
            chat_id=self.chat.id,
            voice=voice,
            caption=caption,
            parse_mode=parse_mode,
            duration=duration,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def answer_voice(
        self,
        voice: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        duration: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> SendVoice:
        """
        Answer with voice

        :param voice:
        :param caption:
        :param parse_mode:
        :param duration:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendVoice

        return SendVoice(
            chat_id=self.chat.id,
            voice=voice,
            caption=caption,
            parse_mode=parse_mode,
            duration=duration,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def send_copy(
        self: Message,
        chat_id: Union[str, int],
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, None] = None,
        allow_sending_without_reply: Optional[bool] = None,
        message_thread_id: Optional[int] = None,
    ) -> Union[
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
        Send copy of message.

        Is similar to :meth:`aiogram.client.bot.Bot.copy_message`
        but returning the sent message instead of :class:`aiogram.types.message_id.MessageId`

        .. note::

            This method don't use the API method named `copyMessage` and
            historically implemented before the similar method is added to API

        :param chat_id:
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :param allow_sending_without_reply:
        :param message_thread_id:
        :return:
        """
        from ..methods import (
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

        kwargs = {
            "chat_id": chat_id,
            "reply_markup": reply_markup or self.reply_markup,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "message_thread_id": message_thread_id,
            "allow_sending_without_reply": allow_sending_without_reply,
        }
        text = self.text or self.caption
        entities = self.entities or self.caption_entities

        if self.text:
            return SendMessage(text=text, entities=entities, **kwargs)
        elif self.audio:
            return SendAudio(
                audio=self.audio.file_id,
                caption=text,
                title=self.audio.title,
                performer=self.audio.performer,
                duration=self.audio.duration,
                caption_entities=entities,
                **kwargs,
            )
        elif self.animation:
            return SendAnimation(
                animation=self.animation.file_id, caption=text, caption_entities=entities, **kwargs
            )
        elif self.document:
            return SendDocument(
                document=self.document.file_id, caption=text, caption_entities=entities, **kwargs
            )
        elif self.photo:
            return SendPhoto(
                photo=self.photo[-1].file_id, caption=text, caption_entities=entities, **kwargs
            )
        elif self.sticker:
            return SendSticker(sticker=self.sticker.file_id, **kwargs)
        elif self.video:
            return SendVideo(
                video=self.video.file_id, caption=text, caption_entities=entities, **kwargs
            )
        elif self.video_note:
            return SendVideoNote(video_note=self.video_note.file_id, **kwargs)
        elif self.voice:
            return SendVoice(voice=self.voice.file_id, **kwargs)
        elif self.contact:
            return SendContact(
                phone_number=self.contact.phone_number,
                first_name=self.contact.first_name,
                last_name=self.contact.last_name,
                vcard=self.contact.vcard,
                **kwargs,
            )
        elif self.venue:
            return SendVenue(
                latitude=self.venue.location.latitude,
                longitude=self.venue.location.longitude,
                title=self.venue.title,
                address=self.venue.address,
                foursquare_id=self.venue.foursquare_id,
                foursquare_type=self.venue.foursquare_type,
                **kwargs,
            )
        elif self.location:
            return SendLocation(
                latitude=self.location.latitude, longitude=self.location.longitude, **kwargs
            )
        elif self.poll:
            return SendPoll(
                question=self.poll.question,
                options=[option.text for option in self.poll.options],
                **kwargs,
            )
        elif self.dice:  # Dice value can't be controlled
            return SendDice(**kwargs)
        else:
            raise TypeError("This type of message can't be copied.")

    def copy_to(
        self,
        chat_id: Union[int, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        message_thread_id: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
        **kwargs: Any,
    ) -> CopyMessage:
        """
        Copy message

        :param chat_id:
        :param caption:
        :param parse_mode:
        :param caption_entities:
        :param message_thread_id:
        :param disable_notification:
        :param reply_to_message_id:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        from ..methods import CopyMessage

        return CopyMessage(
            chat_id=chat_id,
            from_chat_id=self.chat.id,
            message_id=self.message_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            message_thread_id=message_thread_id,
            **kwargs,
        )

    def edit_text(
        self,
        text: str,
        parse_mode: Optional[str] = UNSET,
        entities: Optional[List[MessageEntity]] = None,
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> EditMessageText:
        from ..methods import EditMessageText

        return EditMessageText(
            chat_id=self.chat.id,
            message_id=self.message_id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def forward(
        self,
        chat_id: Union[int, str],
        message_thread_id: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        **kwargs: Any,
    ) -> ForwardMessage:
        from ..methods import ForwardMessage

        return ForwardMessage(
            chat_id=chat_id,
            from_chat_id=self.chat.id,
            message_id=self.message_id,
            disable_notification=disable_notification,
            protect_content=protect_content,
            message_thread_id=message_thread_id,
            **kwargs,
        )

    def edit_media(
        self,
        media: InputMedia,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> EditMessageMedia:
        from ..methods import EditMessageMedia

        return EditMessageMedia(
            media=media,
            chat_id=self.chat.id,
            message_id=self.message_id,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def edit_reply_markup(
        self,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> EditMessageReplyMarkup:
        from ..methods import EditMessageReplyMarkup

        return EditMessageReplyMarkup(
            chat_id=self.chat.id,
            message_id=self.message_id,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def delete_reply_markup(self) -> EditMessageReplyMarkup:
        return self.edit_reply_markup(reply_markup=None)

    def edit_live_location(
        self,
        latitude: float,
        longitude: float,
        horizontal_accuracy: Optional[float] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> EditMessageLiveLocation:
        from ..methods import EditMessageLiveLocation

        return EditMessageLiveLocation(
            latitude=latitude,
            longitude=longitude,
            chat_id=self.chat.id,
            message_id=self.message_id,
            horizontal_accuracy=horizontal_accuracy,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def stop_live_location(
        self,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> StopMessageLiveLocation:
        from ..methods import StopMessageLiveLocation

        return StopMessageLiveLocation(
            chat_id=self.chat.id,
            message_id=self.message_id,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def edit_caption(
        self,
        caption: str,
        parse_mode: Optional[str] = UNSET,
        caption_entities: Optional[List[MessageEntity]] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        **kwargs: Any,
    ) -> EditMessageCaption:
        from ..methods import EditMessageCaption

        return EditMessageCaption(
            chat_id=self.chat.id,
            message_id=self.message_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def delete(
        self,
        **kwargs: Any,
    ) -> DeleteMessage:
        from ..methods import DeleteMessage

        return DeleteMessage(
            chat_id=self.chat.id,
            message_id=self.message_id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def pin(
        self,
        disable_notification: Optional[bool] = None,
        **kwargs: Any,
    ) -> PinChatMessage:
        from ..methods import PinChatMessage

        return PinChatMessage(
            chat_id=self.chat.id,
            message_id=self.message_id,
            disable_notification=disable_notification,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def unpin(
        self,
        **kwargs: Any,
    ) -> UnpinChatMessage:
        from ..methods import UnpinChatMessage

        return UnpinChatMessage(
            chat_id=self.chat.id,
            message_id=self.message_id,
            message_thread_id=self.message_thread_id if self.is_topic_message else None,
            **kwargs,
        )

    def get_url(self, force_private: bool = False) -> Optional[str]:
        """
        Returns message URL. Cannot be used in private (one-to-one) chats.
        If chat has a username, returns URL like https://t.me/username/message_id
        Otherwise (or if {force_private} flag is set), returns https://t.me/c/shifted_chat_id/message_id

        :param force_private: if set, a private URL is returned even for a public chat
        :return: string with full message URL
        """
        if self.chat.type in ("private", "group"):
            return None

        if not self.chat.username or force_private:
            chat_value = f"c/{self.chat.shifted_id}"
        else:
            chat_value = self.chat.username

        return f"https://t.me/{chat_value}/{self.message_id}"


class ContentType(helper.Helper):
    mode = helper.HelperMode.snake_case

    TEXT = helper.Item()  # text
    AUDIO = helper.Item()  # audio
    DOCUMENT = helper.Item()  # document
    ANIMATION = helper.Item()  # animation
    GAME = helper.Item()  # game
    PHOTO = helper.Item()  # photo
    STICKER = helper.Item()  # sticker
    VIDEO = helper.Item()  # video
    VIDEO_NOTE = helper.Item()  # video_note
    VOICE = helper.Item()  # voice
    CONTACT = helper.Item()  # contact
    LOCATION = helper.Item()  # location
    VENUE = helper.Item()  # venue
    NEW_CHAT_MEMBERS = helper.Item()  # new_chat_member
    LEFT_CHAT_MEMBER = helper.Item()  # left_chat_member
    INVOICE = helper.Item()  # invoice
    SUCCESSFUL_PAYMENT = helper.Item()  # successful_payment
    CONNECTED_WEBSITE = helper.Item()  # connected_website
    MIGRATE_TO_CHAT_ID = helper.Item()  # migrate_to_chat_id
    MIGRATE_FROM_CHAT_ID = helper.Item()  # migrate_from_chat_id
    PINNED_MESSAGE = helper.Item()  # pinned_message
    NEW_CHAT_TITLE = helper.Item()  # new_chat_title
    NEW_CHAT_PHOTO = helper.Item()  # new_chat_photo
    DELETE_CHAT_PHOTO = helper.Item()  # delete_chat_photo
    GROUP_CHAT_CREATED = helper.Item()  # group_chat_created
    SUPERGROUP_CHAT_CREATED = helper.Item()  # supergroup_chat_created
    CHANNEL_CHAT_CREATED = helper.Item()  # channel_chat_created
    PASSPORT_DATA = helper.Item()  # passport_data
    PROXIMITY_ALERT_TRIGGERED = helper.Item()  # proximity_alert_triggered
    POLL = helper.Item()  # poll
    DICE = helper.Item()  # dice
    MESSAGE_AUTO_DELETE_TIMER_CHANGED = helper.Item()  # message_auto_delete_timer_changed
    FORUM_TOPIC_CREATED = helper.Item()  # forum_topic_created
    FORUM_TOPIC_CLOSED = helper.Item()  # forum_topic_closed
    FORUM_TOPIC_REOPENED = helper.Item()  # forum_topic_reopened
    VIDEO_CHAT_SCHEDULED = helper.Item()  # video_chat_scheduled
    VIDEO_CHAT_STARTED = helper.Item()  # video_chat_started
    VIDEO_CHAT_ENDED = helper.Item()  # video_chat_ended
    VIDEO_CHAT_PARTICIPANTS_INVITED = helper.Item()  # video_chat_participants_invited
    WEB_APP_DATA = helper.Item()  # web_app_data

    UNKNOWN = helper.Item()  # unknown
    ANY = helper.Item()  # any
