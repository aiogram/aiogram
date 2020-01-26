from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List, Optional, Union

from pydantic import Field

from ...utils import helper
from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .animation import Animation
    from .audio import Audio
    from .chat import Chat
    from .contact import Contact
    from .document import Document
    from .force_reply import ForceReply
    from .game import Game
    from .inline_keyboard_markup import InlineKeyboardMarkup
    from .invoice import Invoice
    from .input_file import InputFile
    from .input_media_photo import InputMediaPhoto
    from .input_media_video import InputMediaVideo
    from .labeled_price import LabeledPrice
    from .location import Location
    from .message_entity import MessageEntity
    from .passport_data import PassportData
    from .photo_size import PhotoSize
    from .poll import Poll
    from .reply_keyboard_markup import ReplyKeyboardMarkup
    from .reply_keyboard_remove import ReplyKeyboardRemove
    from .sticker import Sticker
    from .successful_payment import SuccessfulPayment
    from .user import User
    from .venue import Venue
    from .video import Video
    from .video_note import VideoNote
    from .voice import Voice

    from ..methods import (
        SendAnimation,
        SendAudio,
        SendContact,
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
    )


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
    """Sender's name for messages forwarded from users who disallow adding a link to their account
    in forwarded messages"""
    forward_date: Optional[int] = None
    """For forwarded messages, date the original message was sent in Unix time"""
    reply_to_message: Optional[Message] = None
    """For replies, the original message. Note that the Message object in this field will not
    contain further reply_to_message fields even if it itself is a reply."""
    edit_date: Optional[int] = None
    """Date the message was last edited in Unix time"""
    media_group_id: Optional[str] = None
    """The unique identifier of a media message group this message belongs to"""
    author_signature: Optional[str] = None
    """Signature of the post author for messages in channels"""
    text: Optional[str] = None
    """For text messages, the actual UTF-8 text of the message, 0-4096 characters."""
    entities: Optional[List[MessageEntity]] = None
    """For text messages, special entities like usernames, URLs, bot commands, etc. that appear in
    the text"""
    caption_entities: Optional[List[MessageEntity]] = None
    """For messages with a caption, special entities like usernames, URLs, bot commands, etc. that
    appear in the caption"""
    audio: Optional[Audio] = None
    """Message is an audio file, information about the file"""
    document: Optional[Document] = None
    """Message is a general file, information about the file"""
    animation: Optional[Animation] = None
    """Message is an animation, information about the animation. For backward compatibility, when
    this field is set, the document field will also be set"""
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
    """New members that were added to the group or supergroup and information about them (the bot
    itself may be one of these members)"""
    left_chat_member: Optional[User] = None
    """A member was removed from the group, information about them (this member may be the bot
    itself)"""
    new_chat_title: Optional[str] = None
    """A chat title was changed to this value"""
    new_chat_photo: Optional[List[PhotoSize]] = None
    """A chat photo was change to this value"""
    delete_chat_photo: Optional[bool] = None
    """Service message: the chat photo was deleted"""
    group_chat_created: Optional[bool] = None
    """Service message: the group has been created"""
    supergroup_chat_created: Optional[bool] = None
    """Service message: the supergroup has been created. This field can‘t be received in a message
    coming through updates, because bot can’t be a member of a supergroup when it is created.
    It can only be found in reply_to_message if someone replies to a very first message in a
    directly created supergroup."""
    channel_chat_created: Optional[bool] = None
    """Service message: the channel has been created. This field can‘t be received in a message
    coming through updates, because bot can’t be a member of a channel when it is created. It
    can only be found in reply_to_message if someone replies to a very first message in a
    channel."""
    migrate_to_chat_id: Optional[int] = None
    """The group has been migrated to a supergroup with the specified identifier. This number may
    be greater than 32 bits and some programming languages may have difficulty/silent defects
    in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or
    double-precision float type are safe for storing this identifier."""
    migrate_from_chat_id: Optional[int] = None
    """The supergroup has been migrated from a group with the specified identifier. This number
    may be greater than 32 bits and some programming languages may have difficulty/silent
    defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or
    double-precision float type are safe for storing this identifier."""
    pinned_message: Optional[Message] = None
    """Specified message was pinned. Note that the Message object in this field will not contain
    further reply_to_message fields even if it is itself a reply."""
    invoice: Optional[Invoice] = None
    """Message is an invoice for a payment, information about the invoice."""
    successful_payment: Optional[SuccessfulPayment] = None
    """Message is a service message about a successful payment, information about the payment."""
    connected_website: Optional[str] = None
    """The domain name of the website on which the user has logged in."""
    passport_data: Optional[PassportData] = None
    """Telegram Passport data"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """Inline keyboard attached to the message. login_url buttons are represented as ordinary url
    buttons."""

    @property
    def content_type(self):
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
        if self.passport_data:
            return ContentType.PASSPORT_DATA
        if self.poll:
            return ContentType.POLL

        return ContentType.UNKNOWN

    def reply_animation(
        self,
        animation: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
            reply_markup=reply_markup,
        )

    def answer_animation(
        self,
        animation: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
        )

    def reply_audio(
        self,
        audio: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
            reply_markup=reply_markup,
        )

    def answer_audio(
        self,
        audio: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
        )

    def reply_contact(
        self,
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        vcard: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> SendContact:
        """
        Reply with contact

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
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
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
        )

    def reply_document(
        self,
        document: Union[InputFile, str],
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> SendDocument:
        """
        Reply with document

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
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
        )

    def answer_document(
        self,
        document: Union[InputFile, str],
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
        )

    def reply_game(
        self,
        game_short_name: str,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> SendGame:
        """
        Reply with game

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
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
        )

    def answer_game(
        self,
        game_short_name: str,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
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
        )

    def reply_invoice(
        self,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        start_parameter: str,
        currency: str,
        prices: List[LabeledPrice],
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
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> SendInvoice:
        """
        Reply with invoice

        :param title:
        :param description:
        :param payload:
        :param provider_token:
        :param start_parameter:
        :param currency:
        :param prices:
        :param provider_data:
        :param photo_url:
        :param photo_size:
        :param photo_width:
        :param photo_height:
        :param need_name:
        :param need_phone_number:
        :param need_email:
        :param need_shipping_address:
        :param send_phone_number_to_provider:
        :param send_email_to_provider:
        :param is_flexible:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendInvoice

        return SendInvoice(
            chat_id=self.chat.id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            start_parameter=start_parameter,
            currency=currency,
            prices=prices,
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
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
        )

    def answer_invoice(
        self,
        title: str,
        description: str,
        payload: str,
        provider_token: str,
        start_parameter: str,
        currency: str,
        prices: List[LabeledPrice],
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
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> SendInvoice:
        """
        Answer with invoice

        :param title:
        :param description:
        :param payload:
        :param provider_token:
        :param start_parameter:
        :param currency:
        :param prices:
        :param provider_data:
        :param photo_url:
        :param photo_size:
        :param photo_width:
        :param photo_height:
        :param need_name:
        :param need_phone_number:
        :param need_email:
        :param need_shipping_address:
        :param send_phone_number_to_provider:
        :param send_email_to_provider:
        :param is_flexible:
        :param disable_notification:
        :param reply_markup:
        :return:
        """
        from ..methods import SendInvoice

        return SendInvoice(
            chat_id=self.chat.id,
            title=title,
            description=description,
            payload=payload,
            provider_token=provider_token,
            start_parameter=start_parameter,
            currency=currency,
            prices=prices,
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
            reply_to_message_id=None,
            reply_markup=reply_markup,
        )

    def reply_location(
        self,
        latitude: float,
        longitude: float,
        live_period: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> SendLocation:
        """
        Reply with location

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
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
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
        )

    def reply_media_group(
        self,
        media: List[Union[InputMediaPhoto, InputMediaVideo]],
        disable_notification: Optional[bool] = None,
    ) -> SendMediaGroup:
        """
        Reply with media group

        :param media:
        :param disable_notification:
        :return:
        """
        from ..methods import SendMediaGroup

        return SendMediaGroup(
            chat_id=self.chat.id,
            media=media,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
        )

    def answer_media_group(
        self,
        media: List[Union[InputMediaPhoto, InputMediaVideo]],
        disable_notification: Optional[bool] = None,
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
        )

    def reply(
        self,
        text: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> SendMessage:
        """
        Reply with text message

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
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
        )

    def answer(
        self,
        text: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
        )

    def reply_photo(
        self,
        photo: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> SendPhoto:
        """
        Reply with photo

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
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
        )

    def answer_photo(
        self,
        photo: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
        )

    def reply_poll(
        self,
        question: str,
        options: List[str],
        is_anonymous: Optional[bool] = None,
        type: Optional[str] = None,
        allows_multiple_answers: Optional[bool] = None,
        correct_option_id: Optional[int] = None,
        is_closed: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> SendPoll:
        """
        Reply with poll

        :param question:
        :param options:
        :param is_anonymous:
        :param type:
        :param allows_multiple_answers:
        :param correct_option_id:
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
            is_closed=is_closed,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
        )

    def answer_poll(
        self,
        question: str,
        options: List[str],
        is_anonymous: Optional[bool] = None,
        type: Optional[str] = None,
        allows_multiple_answers: Optional[bool] = None,
        correct_option_id: Optional[int] = None,
        is_closed: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> SendPoll:
        """
        Answer with poll

        :param question:
        :param options:
        :param is_anonymous:
        :param type:
        :param allows_multiple_answers:
        :param correct_option_id:
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
            is_closed=is_closed,
            disable_notification=disable_notification,
            reply_to_message_id=None,
            reply_markup=reply_markup,
        )

    def reply_sticker(
        self,
        sticker: Union[InputFile, str],
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> SendSticker:
        """
        Reply with sticker

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
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
        )

    def answer_sticker(
        self,
        sticker: Union[InputFile, str],
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
            reply_markup=reply_markup,
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
        )

    def reply_video(
        self,
        video: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        supports_streaming: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
            reply_markup=reply_markup,
        )

    def answer_video(
        self,
        video: Union[InputFile, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        supports_streaming: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
        )

    def reply_video_note(
        self,
        video_note: Union[InputFile, str],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        thumb: Optional[Union[InputFile, str]] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> SendVideoNote:
        """
        Reply wit video note

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
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
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
        )

    def reply_voice(
        self,
        voice: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        duration: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
    ) -> SendVoice:
        """
        Reply with voice

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
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
        )

    def answer_voice(
        self,
        voice: Union[InputFile, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        duration: Optional[int] = None,
        disable_notification: Optional[bool] = None,
        reply_markup: Optional[
            Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        ] = None,
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
        )


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
    PASSPORT_DATA = helper.Item()  # passport_data
    POLL = helper.Item()

    UNKNOWN = helper.Item()  # unknown
    ANY = helper.Item()  # any
