from __future__ import annotations

import datetime
import functools
import typing

from . import base, fields
from .animation import Animation
from .audio import Audio
from .chat import Chat, ChatType
from .contact import Contact
from .dice import Dice
from .document import Document
from .force_reply import ForceReply
from .game import Game
from .inline_keyboard import InlineKeyboardMarkup
from .input_media import InputMedia, MediaGroup
from .invoice import Invoice
from .location import Location
from .message_auto_delete_timer_changed import MessageAutoDeleteTimerChanged
from .message_entity import MessageEntity
from .message_id import MessageId
from .passport_data import PassportData
from .photo_size import PhotoSize
from .poll import Poll
from .proximity_alert_triggered import ProximityAlertTriggered
from .reply_keyboard import ReplyKeyboardMarkup, ReplyKeyboardRemove
from .sticker import Sticker
from .successful_payment import SuccessfulPayment
from .user import User
from .venue import Venue
from .video import Video
from .video_note import VideoNote
from .voice import Voice
from .voice_chat_ended import VoiceChatEnded
from .voice_chat_participants_invited import VoiceChatParticipantsInvited
from .voice_chat_scheduled import VoiceChatScheduled
from .voice_chat_started import VoiceChatStarted
from ..utils import helper
from ..utils import markdown as md
from ..utils.text_decorations import html_decoration, markdown_decoration


class Message(base.TelegramObject):
    """
    This object represents a message.

    https://core.telegram.org/bots/api#message
    """

    message_id: base.Integer = fields.Field()
    from_user: User = fields.Field(alias="from", base=User)
    sender_chat: Chat = fields.Field(base=Chat)
    date: datetime.datetime = fields.DateTimeField()
    chat: Chat = fields.Field(base=Chat)
    forward_from: User = fields.Field(base=User)
    forward_from_chat: Chat = fields.Field(base=Chat)
    forward_from_message_id: base.Integer = fields.Field()
    forward_signature: base.String = fields.Field()
    forward_date: datetime.datetime = fields.DateTimeField()
    reply_to_message: Message = fields.Field(base="Message")
    via_bot: User = fields.Field(base=User)
    edit_date: datetime.datetime = fields.DateTimeField()
    media_group_id: base.String = fields.Field()
    author_signature: base.String = fields.Field()
    forward_sender_name: base.String = fields.Field()
    text: base.String = fields.Field()
    entities: typing.List[MessageEntity] = fields.ListField(base=MessageEntity)
    caption_entities: typing.List[MessageEntity] = fields.ListField(base=MessageEntity)
    audio: Audio = fields.Field(base=Audio)
    document: Document = fields.Field(base=Document)
    animation: Animation = fields.Field(base=Animation)
    game: Game = fields.Field(base=Game)
    photo: typing.List[PhotoSize] = fields.ListField(base=PhotoSize)
    sticker: Sticker = fields.Field(base=Sticker)
    video: Video = fields.Field(base=Video)
    voice: Voice = fields.Field(base=Voice)
    video_note: VideoNote = fields.Field(base=VideoNote)
    caption: base.String = fields.Field()
    contact: Contact = fields.Field(base=Contact)
    location: Location = fields.Field(base=Location)
    venue: Venue = fields.Field(base=Venue)
    poll: Poll = fields.Field(base=Poll)
    dice: Dice = fields.Field(base=Dice)
    new_chat_members: typing.List[User] = fields.ListField(base=User)
    left_chat_member: User = fields.Field(base=User)
    new_chat_title: base.String = fields.Field()
    new_chat_photo: typing.List[PhotoSize] = fields.ListField(base=PhotoSize)
    delete_chat_photo: base.Boolean = fields.Field()
    group_chat_created: base.Boolean = fields.Field()
    supergroup_chat_created: base.Boolean = fields.Field()
    channel_chat_created: base.Boolean = fields.Field()
    message_auto_delete_timer_changed: MessageAutoDeleteTimerChanged = fields.Field(base=MessageAutoDeleteTimerChanged)
    migrate_to_chat_id: base.Integer = fields.Field()
    migrate_from_chat_id: base.Integer = fields.Field()
    pinned_message: Message = fields.Field(base="Message")
    invoice: Invoice = fields.Field(base=Invoice)
    successful_payment: SuccessfulPayment = fields.Field(base=SuccessfulPayment)
    connected_website: base.String = fields.Field()
    passport_data: PassportData = fields.Field(base=PassportData)
    proximity_alert_triggered: ProximityAlertTriggered = fields.Field(base=ProximityAlertTriggered)
    voice_chat_scheduled: VoiceChatScheduled = fields.Field(base=VoiceChatScheduled)
    voice_chat_started: VoiceChatStarted = fields.Field(base=VoiceChatStarted)
    voice_chat_ended: VoiceChatEnded = fields.Field(base=VoiceChatEnded)
    voice_chat_participants_invited: VoiceChatParticipantsInvited = fields.Field(base=VoiceChatParticipantsInvited)
    reply_markup: InlineKeyboardMarkup = fields.Field(base=InlineKeyboardMarkup)

    @property
    @functools.lru_cache()
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
        if self.poll:
            return ContentType.POLL
        if self.dice:
            return ContentType.DICE
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
        if self.message_auto_delete_timer_changed:
            return ContentType.MESSAGE_AUTO_DELETE_TIMER_CHANGED
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
        if self.proximity_alert_triggered:
            return ContentType.PROXIMITY_ALERT_TRIGGERED
        if self.voice_chat_scheduled:
            return ContentType.VOICE_CHAT_SCHEDULED
        if self.voice_chat_started:
            return ContentType.VOICE_CHAT_STARTED
        if self.voice_chat_ended:
            return ContentType.VOICE_CHAT_ENDED
        if self.voice_chat_participants_invited:
            return ContentType.VOICE_CHAT_PARTICIPANTS_INVITED

        return ContentType.UNKNOWN

    def is_forward(self) -> bool:
        """
        Check that the message is forwarded.
        Only `forward_date` is required to be in forwarded message.

        :return: bool
        """
        return bool(self.forward_date)

    def is_command(self) -> bool:
        """
        Check message text is command

        :return: bool
        """
        text = self.text or self.caption
        return text and text.startswith("/")

    def get_full_command(self) -> typing.Optional[typing.Tuple[str, str]]:
        """
        Split command and args

        :return: tuple of (command, args)
        """
        if self.is_command():
            text = self.text or self.caption
            command, *args = text.split(maxsplit=1)
            args = args[0] if args else ""
            return command, args

    def get_command(self, pure=False) -> typing.Optional[str]:
        """
        Get command from message

        :return:
        """
        command = self.get_full_command()
        if command:
            command = command[0]
            if pure:
                command, _, _ = command[1:].partition("@")
            return command

    def get_args(self) -> typing.Optional[str]:
        """
        Get arguments

        :return:
        """
        command = self.get_full_command()
        if command:
            return command[1]

    def parse_entities(self, as_html=True) -> str:
        """
        Text or caption formatted as HTML or Markdown.

        :return: str
        """

        text = self.text or self.caption
        if text is None:
            raise TypeError("This message doesn't have any text.")

        entities = self.entities or self.caption_entities
        text_decorator = html_decoration if as_html else markdown_decoration

        return text_decorator.unparse(text, entities)

    @property
    def md_text(self) -> str:
        """
        Text or caption formatted as markdown.

        :return: str
        """
        return self.parse_entities(False)

    @property
    def html_text(self) -> str:
        """
        Text or caption formatted as HTML

        :return: str
        """
        return self.parse_entities()

    @property
    def url(self) -> str:
        """
        Get URL for the message

        :return: str
        """

        if self.chat.type == ChatType.PRIVATE:
            raise TypeError("Invalid chat type!")
        url = "https://t.me/"
        if self.chat.username:
            # Generates public link
            url += f"{self.chat.username}/"
        else:
            # Generates private link available for chat members
            url += f"c/{self.chat.shifted_id}/"
        url += f"{self.message_id}"

        return url

    def link(self, text, as_html=True) -> str:
        """
        Generate URL for using in text messages with HTML or MD parse mode

        :param text: link label
        :param as_html: generate as HTML
        :return: str
        """
        try:
            url = self.url
        except TypeError:  # URL is not accessible
            if as_html:
                return md.quote_html(text)
            return md.escape_md(text)

        if as_html:
            return md.hlink(text, url)
        return md.link(text, url)

    async def answer(
        self,
        text: base.String,
        parse_mode: typing.Optional[base.String] = None,
        entities: typing.Optional[typing.List[MessageEntity]] = None,
        disable_web_page_preview: typing.Optional[base.Boolean] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Answer to this message

        :param text: Text of the message to be sent
        :type text: :obj:`base.String`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param disable_web_page_preview: Disables link previews for links in this message
        :type disable_web_page_preview: :obj:`typing.Optional[base.Boolean]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_message(
            chat_id=self.chat.id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_photo(
        self,
        photo: typing.Union[base.InputFile, base.String],
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send photos.

        Source: https://core.telegram.org/bots/api#sendphoto

        :param photo: Photo to send
        :type photo: :obj:`typing.Union[base.InputFile, base.String]`

        :param caption: Photo caption (may also be used when resending photos by file_id), 0-1024 characters
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_photo(
            chat_id=self.chat.id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_audio(
        self,
        audio: typing.Union[base.InputFile, base.String],
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        duration: typing.Optional[base.Integer] = None,
        performer: typing.Optional[base.String] = None,
        title: typing.Optional[base.String] = None,
        thumb: typing.Union[typing.Union[base.InputFile, base.String], None] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player.
        Your audio must be in the .mp3 format.

        For sending voice messages, use the sendVoice method instead.

        Source: https://core.telegram.org/bots/api#sendaudio

        :param audio: Audio file to send.
        :type audio: :obj:`typing.Union[base.InputFile, base.String]`

        :param caption: Audio caption, 0-1024 characters after entities parsing
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param duration: Duration of the audio in seconds
        :type duration: :obj:`typing.Optional[base.Integer]`

        :param performer: Performer
        :type performer: :obj:`typing.Optional[base.String]`

        :param title: Track name
        :type title: :obj:`typing.Optional[base.String]`

        :param thumb: Thumbnail of the file sent. The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail‘s width and height should not exceed 320.
        :type thumb: :obj:`typing.Union[typing.Union[base.InputFile, base.String], None]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_audio(
            chat_id=self.chat.id,
            audio=audio,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_animation(
        self,
        animation: typing.Union[base.InputFile, base.String],
        duration: typing.Optional[base.Integer] = None,
        width: typing.Optional[base.Integer] = None,
        height: typing.Optional[base.Integer] = None,
        thumb: typing.Union[typing.Union[base.InputFile, base.String], None] = None,
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound).

        On success, the sent Message is returned.
        Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.

        Source https://core.telegram.org/bots/api#sendanimation

        :param animation: Animation to send. Pass a file_id as String to send an animation that exists
            on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation
            from the Internet, or upload a new animation using multipart/form-data
        :type animation: :obj:`typing.Union[base.InputFile, base.String]`

        :param duration: Duration of sent animation in seconds
        :type duration: :obj:`typing.Optional[base.Integer]`

        :param width: Animation width
        :type width: :obj:`typing.Optional[base.Integer]`

        :param height: Animation height
        :type height: :obj:`typing.Optional[base.Integer]`

        :param thumb: Thumbnail of the file sent. The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail‘s width and height should not exceed 320.
        :type thumb: :obj:`typing.Union[typing.Union[base.InputFile, base.String], None]`

        :param caption: Animation caption (may also be used when resending animation by file_id), 0-1024 characters
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in the media caption
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[typing.Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup,
            types.ReplyKeyboardRemove, types.ForceReply], None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_animation(
            self.chat.id,
            animation=animation,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_document(
        self,
        document: typing.Union[base.InputFile, base.String],
        thumb: typing.Union[typing.Union[base.InputFile, base.String], None] = None,
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        disable_content_type_detection: typing.Optional[base.Boolean] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send general files. On success, the sent Message is
        returned. Bots can currently send files of any type of up to 50 MB in size,
        this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#senddocument

        :param document: File to send
        :type document: :obj:`typing.Union[base.InputFile, base.String]`

        :param thumb: Thumbnail of the file sent
        :type thumb: :obj:`typing.Union[base.InputFile, base.String, None]`

        :param caption: Document caption (may also be used when resending documents
            by file_id), 0-1024 characters
        :type caption: :obj:`typing.Optional[base.String]`

        :param disable_content_type_detection: Disables automatic server-side content
            type detection for files uploaded using multipart/form-data
        :type disable_content_type_detection: :obj:`typing.Optional[base.Boolean]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show
            bold, italic, fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param disable_notification: Sends the message silently. Users will receive a
            notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object
            for an inline keyboard, custom reply keyboard, instructions to remove
            reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply],
            None]`

        :param reply: True if the message is a reply
        :type reply: :obj:`typing.Optional[base.Boolean]`

        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_document(
            chat_id=self.chat.id,
            thumb=thumb,
            document=document,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_content_type_detection=disable_content_type_detection,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_video(
        self,
        video: typing.Union[base.InputFile, base.String],
        duration: typing.Optional[base.Integer] = None,
        width: typing.Optional[base.Integer] = None,
        height: typing.Optional[base.Integer] = None,
        thumb: typing.Union[base.InputFile, base.String, None] = None,
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        supports_streaming: typing.Optional[base.Boolean] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send video files, Telegram clients support mp4 videos
        (other formats may be sent as Document).

        Source: https://core.telegram.org/bots/api#sendvideo

        :param video: Video to send.
        :type video: :obj:`typing.Union[base.InputFile, base.String]`

        :param duration: Duration of sent video in seconds
        :type duration: :obj:`typing.Optional[base.Integer]`

        :param width: Video width
        :type width: :obj:`typing.Optional[base.Integer]`

        :param height: Video height
        :type height: :obj:`typing.Optional[base.Integer]`

        :param thumb: Thumbnail of the file sent. The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail‘s width and height should not exceed 320.
        :type thumb: :obj:`typing.Union[base.InputFile, base.String, None]`

        :param caption: Video caption (may also be used when resending videos by file_id), 0-1024 characters after entities parsing
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in the media caption
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param supports_streaming: Pass True, if the uploaded video is suitable for streaming
        :type supports_streaming: :obj:`typing.Optional[base.Boolean]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_video(
            chat_id=self.chat.id,
            video=video,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            supports_streaming=supports_streaming,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_voice(
        self,
        voice: typing.Union[base.InputFile, base.String],
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        duration: typing.Optional[base.Integer] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file
        as a playable voice message.

        For this to work, your audio must be in an .ogg file encoded with OPUS
        (other formats may be sent as Audio or Document).

        Source: https://core.telegram.org/bots/api#sendvoice

        :param voice: Audio file to send.
        :type voice: :obj:`typing.Union[base.InputFile, base.String]`

        :param caption: Voice message caption, 0-1024 characters after entities parsing
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in the media caption
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param duration: Duration of the voice message in seconds
        :type duration: :obj:`typing.Optional[base.Integer]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_voice(
            chat_id=self.chat.id,
            voice=voice,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_video_note(
        self,
        video_note: typing.Union[base.InputFile, base.String],
        duration: typing.Optional[base.Integer] = None,
        length: typing.Optional[base.Integer] = None,
        thumb: typing.Union[typing.Union[base.InputFile, base.String], None] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long.
        Use this method to send video messages.

        Source: https://core.telegram.org/bots/api#sendvideonote

        :param video_note: Video note to send.
        :type video_note: :obj:`typing.Union[base.InputFile, base.String]`

        :param duration: Duration of sent video in seconds
        :type duration: :obj:`typing.Optional[base.Integer]`

        :param length: Video width and height
        :type length: :obj:`typing.Optional[base.Integer]`

        :param thumb: Thumbnail of the file sent. The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail‘s width and height should not exceed 320.
        :type thumb: :obj:`typing.Union[typing.Union[base.InputFile, base.String], None]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_video_note(
            chat_id=self.chat.id,
            video_note=video_note,
            duration=duration,
            length=length,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_media_group(
        self,
        media: typing.Union[MediaGroup, typing.List],
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply: base.Boolean = False,
    ) -> typing.List[Message]:
        """
        Use this method to send a group of photos, videos, documents or audios as
        an album. Documents and audio files can be only group in an album with
        messages of the same type. On success, an array of Messages that were sent
        is returned.

        Source: https://core.telegram.org/bots/api#sendmediagroup

        :param media: A JSON-serialized array describing photos and videos to be sent
        :type media: :obj:`typing.Union[types.MediaGroup, typing.List]`

        :param disable_notification: Sends the message silently. Users will receive
            a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, an array of the sent Messages is returned.
        :rtype: typing.List[types.Message]
        """
        return await self.bot.send_media_group(
            self.chat.id,
            media=media,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
        )

    async def answer_location(
        self,
        latitude: base.Float,
        longitude: base.Float,
        live_period: typing.Optional[base.Integer] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        horizontal_accuracy: typing.Optional[base.Float] = None,
        heading: typing.Optional[base.Integer] = None,
        proximity_alert_radius: typing.Optional[base.Integer] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send point on the map.

        Source: https://core.telegram.org/bots/api#sendlocation

        :param latitude: Latitude of the location
        :type latitude: :obj:`base.Float`

        :param longitude: Longitude of the location
        :type longitude: :obj:`base.Float`

        :param horizontal_accuracy: The radius of uncertainty for the location,
            measured in meters; 0-1500
        :type horizontal_accuracy: :obj:`typing.Optional[base.Float]`

        :param live_period: Period in seconds for which the location will be updated
        :type live_period: :obj:`typing.Optional[base.Integer]`

        :param heading: For live locations, a direction in which the user is moving,
            in degrees. Must be between 1 and 360 if specified.
        :type heading: :obj:`typing.Optional[base.Integer]`

        :param proximity_alert_radius: For live locations, a maximum distance for
            proximity alerts about approaching another chat member, in meters. Must
            be between 1 and 100000 if specified.
        :type proximity_alert_radius: :obj:`typing.Optional[base.Integer]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_location(
            chat_id=self.chat.id,
            latitude=latitude,
            longitude=longitude,
            horizontal_accuracy=horizontal_accuracy,
            live_period=live_period,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_venue(
        self,
        latitude: base.Float,
        longitude: base.Float,
        title: base.String,
        address: base.String,
        foursquare_id: typing.Optional[base.String] = None,
        foursquare_type: typing.Optional[base.String] = None,
        google_place_id: typing.Optional[base.String] = None,
        google_place_type: typing.Optional[base.String] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send information about a venue.

        Source: https://core.telegram.org/bots/api#sendvenue

        :param latitude: Latitude of the venue
        :type latitude: :obj:`base.Float`

        :param longitude: Longitude of the venue
        :type longitude: :obj:`base.Float`

        :param title: Name of the venue
        :type title: :obj:`base.String`

        :param address: Address of the venue
        :type address: :obj:`base.String`

        :param foursquare_id: Foursquare identifier of the venue
        :type foursquare_id: :obj:`typing.Optional[base.String]`

        :param foursquare_type: Foursquare type of the venue, if known
        :type foursquare_type: :obj:`typing.Optional[base.String]`

        :param google_place_id: Google Places identifier of the venue
        :type google_place_id: :obj:`typing.Optional[base.String]`

        :param google_place_type: Google Places type of the venue. See supported
            types: https://developers.google.com/places/web-service/supported_types
        :type google_place_type: :obj:`typing.Optional[base.String]`

        :param disable_notification: Sends the message silently. Users will receive
            a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object
            for an inline keyboard, custom reply keyboard, instructions to remove
            reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply,
            None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_venue(
            chat_id=self.chat.id,
            latitude=latitude,
            longitude=longitude,
            title=title,
            address=address,
            foursquare_id=foursquare_id,
            foursquare_type=foursquare_type,
            google_place_id=google_place_id,
            google_place_type=google_place_type,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_contact(
        self,
        phone_number: base.String,
        first_name: base.String,
        last_name: typing.Optional[base.String] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send phone contacts.

        Source: https://core.telegram.org/bots/api#sendcontact

        :param phone_number: Contact's phone number
        :type phone_number: :obj:`base.String`

        :param first_name: Contact's first name
        :type first_name: :obj:`base.String`

        :param last_name: Contact's last name
        :type last_name: :obj:`typing.Optional[base.String]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_contact(
            chat_id=self.chat.id,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_sticker(
        self,
        sticker: typing.Union[base.InputFile, base.String],
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send .webp stickers.

        Source: https://core.telegram.org/bots/api#sendsticker

        :param sticker: Sticker to send.
        :type sticker: :obj:`typing.Union[base.InputFile, base.String]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_sticker(
            chat_id=self.chat.id,
            sticker=sticker,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_poll(
        self,
        question: base.String,
        options: typing.List[base.String],
        is_anonymous: typing.Optional[base.Boolean] = None,
        type: typing.Optional[base.String] = None,
        allows_multiple_answers: typing.Optional[base.Boolean] = None,
        correct_option_id: typing.Optional[base.Integer] = None,
        explanation: typing.Optional[base.String] = None,
        explanation_parse_mode: typing.Optional[base.String] = None,
        explanation_entities: typing.Optional[typing.List[MessageEntity]] = None,
        open_period: typing.Optional[base.Integer] = None,
        close_date: typing.Union[base.Integer, datetime.datetime, datetime.timedelta, None] = None,
        is_closed: typing.Optional[base.Boolean] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send a native poll. On success, the sent Message is
        returned.

        Source: https://core.telegram.org/bots/api#sendpoll

        :param question: Poll question, 1-255 characters
        :type question: :obj:`base.String`

        :param options: List of answer options, 2-10 strings 1-100 characters each
        :type options: :obj:`typing.List[base.String]`

        :param is_anonymous: True, if the poll needs to be anonymous, defaults to True
        :type is_anonymous: :obj:`typing.Optional[base.Boolean]`

        :param type: Poll type, “quiz” or “regular”, defaults to “regular”
        :type type: :obj:`typing.Optional[base.String]`

        :param allows_multiple_answers: True, if the poll allows multiple answers,
            ignored for polls in quiz mode, defaults to False
        :type allows_multiple_answers: :obj:`typing.Optional[base.Boolean]`

        :param correct_option_id: 0-based identifier of the correct answer option,
            required for polls in quiz mode
        :type correct_option_id: :obj:`typing.Optional[base.Integer]`

        :param explanation: Text that is shown when a user chooses an incorrect
            answer or taps on the lamp icon in a quiz-style poll, 0-200 characters
            with at most 2 line feeds after entities parsing
        :type explanation: :obj:`typing.Optional[base.String]`

        :param explanation_parse_mode: Mode for parsing entities in the explanation.
            See formatting options for more details.
        :type explanation_parse_mode: :obj:`typing.Optional[base.String]`

        :param explanation_entities: List of special entities that appear in message
            text, which can be specified instead of parse_mode
        :type explanation_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param open_period: Amount of time in seconds the poll will be active after
            creation, 5-600. Can't be used together with close_date.
        :type open_period: :obj:`typing.Optional[base.Integer]`

        :param close_date: Point in time (Unix timestamp) when the poll will be
            automatically closed. Must be at least 5 and no more than 600 seconds in
            the future. Can't be used together with open_period.
        :type close_date: :obj:`typing.Union[base.Integer, datetime.datetime,
            datetime.timedelta, None]`

        :param is_closed: Pass True, if the poll needs to be immediately closed
        :type is_closed: :obj:`typing.Optional[base.Boolean]`

        :param disable_notification: Sends the message silently. Users will receive
            a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object
            for an inline keyboard, custom reply keyboard, instructions to remove
            reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply,
            None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_poll(
            chat_id=self.chat.id,
            question=question,
            options=options,
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
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_dice(
        self,
        emoji: typing.Optional[base.String] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = False,
    ) -> Message:
        """
        Use this method to send an animated emoji that will display a random value.
        On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#senddice

        :param emoji: Emoji on which the dice throw animation is based. Currently,
            must be one of “🎲”, “🎯”, “🏀”, “⚽”, or “🎰”. Dice can have values 1-6
            for “🎲” and “🎯”, values 1-5 for “🏀” and “⚽”, and values 1-64 for “🎰”.
            Defaults to “🎲”
        :type emoji: :obj:`typing.Optional[base.String]`

        :param disable_notification: Sends the message silently. Users will receive
            a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object
            for an inline keyboard, custom reply keyboard, instructions to remove
            reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply,
            None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_dice(
            chat_id=self.chat.id,
            emoji=emoji,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def answer_chat_action(
        self,
        action: base.String,
    ) -> base.Boolean:
        """
        Use this method when you need to tell the user that something is happening on the bot's side.
        The status is set for 5 seconds or less
        (when a message arrives from your bot, Telegram clients clear its typing status).

        We only recommend using this method when a response from the bot will take
        a noticeable amount of time to arrive.

        Source: https://core.telegram.org/bots/api#sendchataction

        :param action: Type of action to broadcast
        :type action: :obj:`base.String`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        return await self.bot.send_chat_action(
            chat_id=self.chat.id,
            action=action,
        )

    async def reply(
        self,
        text: base.String,
        parse_mode: typing.Optional[base.String] = None,
        entities: typing.Optional[typing.List[MessageEntity]] = None,
        disable_web_page_preview: typing.Optional[base.Boolean] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Reply to this message

        :param text: Text of the message to be sent
        :type text: :obj:`base.String`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param disable_web_page_preview: Disables link previews for links in this message
        :type disable_web_page_preview: :obj:`typing.Optional[base.Boolean]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_message(
            chat_id=self.chat.id,
            text=text,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_photo(
        self,
        photo: typing.Union[base.InputFile, base.String],
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send photos.

        Source: https://core.telegram.org/bots/api#sendphoto

        :param photo: Photo to send
        :type photo: :obj:`typing.Union[base.InputFile, base.String]`

        :param caption: Photo caption (may also be used when resending photos by file_id), 0-1024 characters
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_photo(
            chat_id=self.chat.id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_audio(
        self,
        audio: typing.Union[base.InputFile, base.String],
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        duration: typing.Optional[base.Integer] = None,
        performer: typing.Optional[base.String] = None,
        title: typing.Optional[base.String] = None,
        thumb: typing.Union[typing.Union[base.InputFile, base.String], None] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player.
        Your audio must be in the .mp3 format.

        For sending voice messages, use the sendVoice method instead.

        Source: https://core.telegram.org/bots/api#sendaudio

        :param audio: Audio file to send.
        :type audio: :obj:`typing.Union[base.InputFile, base.String]`

        :param caption: Audio caption, 0-1024 characters after entities parsing
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param duration: Duration of the audio in seconds
        :type duration: :obj:`typing.Optional[base.Integer]`

        :param performer: Performer
        :type performer: :obj:`typing.Optional[base.String]`

        :param title: Track name
        :type title: :obj:`typing.Optional[base.String]`

        :param thumb: Thumbnail of the file sent. The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail‘s width and height should not exceed 320.
        :type thumb: :obj:`typing.Union[typing.Union[base.InputFile, base.String], None]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_audio(
            chat_id=self.chat.id,
            audio=audio,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_animation(
        self,
        animation: typing.Union[base.InputFile, base.String],
        duration: typing.Optional[base.Integer] = None,
        width: typing.Optional[base.Integer] = None,
        height: typing.Optional[base.Integer] = None,
        thumb: typing.Union[typing.Union[base.InputFile, base.String], None] = None,
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound).

        On success, the sent Message is returned.
        Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.

        Source https://core.telegram.org/bots/api#sendanimation

        :param animation: Animation to send. Pass a file_id as String to send an animation that exists
            on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation
            from the Internet, or upload a new animation using multipart/form-data
        :type animation: :obj:`typing.Union[base.InputFile, base.String]`

        :param duration: Duration of sent animation in seconds
        :type duration: :obj:`typing.Optional[base.Integer]`

        :param width: Animation width
        :type width: :obj:`typing.Optional[base.Integer]`

        :param height: Animation height
        :type height: :obj:`typing.Optional[base.Integer]`

        :param thumb: Thumbnail of the file sent. The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail‘s width and height should not exceed 320.
        :type thumb: :obj:`typing.Union[typing.Union[base.InputFile, base.String], None]`

        :param caption: Animation caption (may also be used when resending animation by file_id), 0-1024 characters
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in the media caption
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[typing.Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup,
            types.ReplyKeyboardRemove, types.ForceReply], None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_animation(
            self.chat.id,
            animation=animation,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_document(
        self,
        document: typing.Union[base.InputFile, base.String],
        thumb: typing.Union[typing.Union[base.InputFile, base.String], None] = None,
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        disable_content_type_detection: typing.Optional[base.Boolean] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send general files. On success, the sent Message is
        returned. Bots can currently send files of any type of up to 50 MB in size,
        this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#senddocument

        :param document: File to send
        :type document: :obj:`typing.Union[base.InputFile, base.String]`

        :param thumb: Thumbnail of the file sent
        :type thumb: :obj:`typing.Union[base.InputFile, base.String, None]`

        :param caption: Document caption (may also be used when resending documents
            by file_id), 0-1024 characters
        :type caption: :obj:`typing.Optional[base.String]`

        :param disable_content_type_detection: Disables automatic server-side content
            type detection for files uploaded using multipart/form-data
        :type disable_content_type_detection: :obj:`typing.Optional[base.Boolean]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show
            bold, italic, fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param disable_notification: Sends the message silently. Users will receive a
            notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object
            for an inline keyboard, custom reply keyboard, instructions to remove
            reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply],
            None]`

        :param reply: True if the message is a reply
        :type reply: :obj:`typing.Optional[base.Boolean]`

        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_document(
            chat_id=self.chat.id,
            document=document,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_content_type_detection=disable_content_type_detection,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_video(
        self,
        video: typing.Union[base.InputFile, base.String],
        duration: typing.Optional[base.Integer] = None,
        width: typing.Optional[base.Integer] = None,
        height: typing.Optional[base.Integer] = None,
        thumb: typing.Union[base.InputFile, base.String, None] = None,
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        supports_streaming: typing.Optional[base.Boolean] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send video files, Telegram clients support mp4 videos
        (other formats may be sent as Document).

        Source: https://core.telegram.org/bots/api#sendvideo

        :param video: Video to send.
        :type video: :obj:`typing.Union[base.InputFile, base.String]`

        :param duration: Duration of sent video in seconds
        :type duration: :obj:`typing.Optional[base.Integer]`

        :param width: Video width
        :type width: :obj:`typing.Optional[base.Integer]`

        :param height: Video height
        :type height: :obj:`typing.Optional[base.Integer]`

        :param thumb: Thumbnail of the file sent. The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail‘s width and height should not exceed 320.
        :type thumb: :obj:`typing.Union[base.InputFile, base.String, None]`

        :param caption: Video caption (may also be used when resending videos by file_id), 0-1024 characters after entities parsing
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in the media caption
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param supports_streaming: Pass True, if the uploaded video is suitable for streaming
        :type supports_streaming: :obj:`typing.Optional[base.Boolean]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_video(
            chat_id=self.chat.id,
            video=video,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            supports_streaming=supports_streaming,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_voice(
        self,
        voice: typing.Union[base.InputFile, base.String],
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        duration: typing.Optional[base.Integer] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file
        as a playable voice message.

        For this to work, your audio must be in an .ogg file encoded with OPUS
        (other formats may be sent as Audio or Document).

        Source: https://core.telegram.org/bots/api#sendvoice

        :param voice: Audio file to send.
        :type voice: :obj:`typing.Union[base.InputFile, base.String]`

        :param caption: Voice message caption, 0-1024 characters after entities parsing
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in the media caption
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param duration: Duration of the voice message in seconds
        :type duration: :obj:`typing.Optional[base.Integer]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_voice(
            chat_id=self.chat.id,
            voice=voice,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            duration=duration,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_video_note(
        self,
        video_note: typing.Union[base.InputFile, base.String],
        duration: typing.Optional[base.Integer] = None,
        length: typing.Optional[base.Integer] = None,
        thumb: typing.Union[typing.Union[base.InputFile, base.String], None] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long.
        Use this method to send video messages.

        Source: https://core.telegram.org/bots/api#sendvideonote

        :param video_note: Video note to send.
        :type video_note: :obj:`typing.Union[base.InputFile, base.String]`

        :param duration: Duration of sent video in seconds
        :type duration: :obj:`typing.Optional[base.Integer]`

        :param length: Video width and height
        :type length: :obj:`typing.Optional[base.Integer]`

        :param thumb: Thumbnail of the file sent. The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail‘s width and height should not exceed 320.
        :type thumb: :obj:`typing.Union[typing.Union[base.InputFile, base.String], None]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]
            `
        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_video_note(
            chat_id=self.chat.id,
            video_note=video_note,
            duration=duration,
            length=length,
            thumb=thumb,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_media_group(
        self,
        media: typing.Union[MediaGroup, typing.List],
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply: base.Boolean = True,
    ) -> typing.List[Message]:
        """
        Use this method to send a group of photos, videos, documents or audios as
        an album. Documents and audio files can be only group in an album with
        messages of the same type. On success, an array of Messages that were sent
        is returned.

        Source: https://core.telegram.org/bots/api#sendmediagroup

        :param media: A JSON-serialized array describing photos and videos to be sent
        :type media: :obj:`typing.Union[types.MediaGroup, typing.List]`

        :param disable_notification: Sends the message silently. Users will receive
            a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, an array of the sent Messages is returned.
        :rtype: typing.List[types.Message]
        """
        return await self.bot.send_media_group(
            self.chat.id,
            media=media,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
        )

    async def reply_location(
        self,
        latitude: base.Float,
        longitude: base.Float,
        live_period: typing.Optional[base.Integer] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        horizontal_accuracy: typing.Optional[base.Float] = None,
        heading: typing.Optional[base.Integer] = None,
        proximity_alert_radius: typing.Optional[base.Integer] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send point on the map.

        Source: https://core.telegram.org/bots/api#sendlocation

        :param latitude: Latitude of the location
        :type latitude: :obj:`base.Float`

        :param longitude: Longitude of the location
        :type longitude: :obj:`base.Float`

        :param horizontal_accuracy: The radius of uncertainty for the location,
            measured in meters; 0-1500
        :type horizontal_accuracy: :obj:`typing.Optional[base.Float]`

        :param live_period: Period in seconds for which the location will be updated
        :type live_period: :obj:`typing.Optional[base.Integer]`

        :param heading: For live locations, a direction in which the user is moving,
            in degrees. Must be between 1 and 360 if specified.
        :type heading: :obj:`typing.Optional[base.Integer]`

        :param proximity_alert_radius: For live locations, a maximum distance for
            proximity alerts about approaching another chat member, in meters. Must
            be between 1 and 100000 if specified.
        :type proximity_alert_radius: :obj:`typing.Optional[base.Integer]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_location(
            chat_id=self.chat.id,
            latitude=latitude,
            longitude=longitude,
            horizontal_accuracy=horizontal_accuracy,
            live_period=live_period,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            reply_markup=reply_markup,
        )

    async def reply_venue(
        self,
        latitude: base.Float,
        longitude: base.Float,
        title: base.String,
        address: base.String,
        foursquare_id: typing.Optional[base.String] = None,
        foursquare_type: typing.Optional[base.String] = None,
        google_place_id: typing.Optional[base.String] = None,
        google_place_type: typing.Optional[base.String] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send information about a venue.

        Source: https://core.telegram.org/bots/api#sendvenue

        :param latitude: Latitude of the venue
        :type latitude: :obj:`base.Float`

        :param longitude: Longitude of the venue
        :type longitude: :obj:`base.Float`

        :param title: Name of the venue
        :type title: :obj:`base.String`

        :param address: Address of the venue
        :type address: :obj:`base.String`

        :param foursquare_id: Foursquare identifier of the venue
        :type foursquare_id: :obj:`typing.Optional[base.String]`

        :param foursquare_type: Foursquare type of the venue, if known
        :type foursquare_type: :obj:`typing.Optional[base.String]`

        :param google_place_id: Google Places identifier of the venue
        :type google_place_id: :obj:`typing.Optional[base.String]`

        :param google_place_type: Google Places type of the venue. See supported
            types: https://developers.google.com/places/web-service/supported_types
        :type google_place_type: :obj:`typing.Optional[base.String]`

        :param disable_notification: Sends the message silently. Users will receive
            a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object
            for an inline keyboard, custom reply keyboard, instructions to remove
            reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply,
            None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_venue(
            chat_id=self.chat.id,
            latitude=latitude,
            longitude=longitude,
            title=title,
            address=address,
            foursquare_id=foursquare_id,
            foursquare_type=foursquare_type,
            google_place_id=google_place_id,
            google_place_type=google_place_type,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_contact(
        self,
        phone_number: base.String,
        first_name: base.String,
        last_name: typing.Optional[base.String] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send phone contacts.

        Source: https://core.telegram.org/bots/api#sendcontact

        :param phone_number: Contact's phone number
        :type phone_number: :obj:`base.String`

        :param first_name: Contact's first name
        :type first_name: :obj:`base.String`

        :param last_name: Contact's last name
        :type last_name: :obj:`typing.Optional[base.String]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_contact(
            chat_id=self.chat.id,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_poll(
        self,
        question: base.String,
        options: typing.List[base.String],
        is_anonymous: typing.Optional[base.Boolean] = None,
        type: typing.Optional[base.String] = None,
        allows_multiple_answers: typing.Optional[base.Boolean] = None,
        correct_option_id: typing.Optional[base.Integer] = None,
        explanation: typing.Optional[base.String] = None,
        explanation_parse_mode: typing.Optional[base.String] = None,
        explanation_entities: typing.Optional[typing.List[MessageEntity]] = None,
        open_period: typing.Optional[base.Integer] = None,
        close_date: typing.Union[base.Integer, datetime.datetime, datetime.timedelta, None] = None,
        is_closed: typing.Optional[base.Boolean] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send a native poll. On success, the sent Message is
        returned.

        Source: https://core.telegram.org/bots/api#sendpoll

        :param question: Poll question, 1-255 characters
        :type question: :obj:`base.String`

        :param options: List of answer options, 2-10 strings 1-100 characters each
        :type options: :obj:`typing.List[base.String]`

        :param is_anonymous: True, if the poll needs to be anonymous, defaults to True
        :type is_anonymous: :obj:`typing.Optional[base.Boolean]`

        :param type: Poll type, “quiz” or “regular”, defaults to “regular”
        :type type: :obj:`typing.Optional[base.String]`

        :param allows_multiple_answers: True, if the poll allows multiple answers,
            ignored for polls in quiz mode, defaults to False
        :type allows_multiple_answers: :obj:`typing.Optional[base.Boolean]`

        :param correct_option_id: 0-based identifier of the correct answer option,
            required for polls in quiz mode
        :type correct_option_id: :obj:`typing.Optional[base.Integer]`

        :param explanation: Text that is shown when a user chooses an incorrect
            answer or taps on the lamp icon in a quiz-style poll, 0-200 characters
            with at most 2 line feeds after entities parsing
        :type explanation: :obj:`typing.Optional[base.String]`

        :param explanation_parse_mode: Mode for parsing entities in the explanation.
            See formatting options for more details.
        :type explanation_parse_mode: :obj:`typing.Optional[base.String]`

        :param explanation_entities: List of special entities that appear in message
            text, which can be specified instead of parse_mode
        :type explanation_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param open_period: Amount of time in seconds the poll will be active after
            creation, 5-600. Can't be used together with close_date.
        :type open_period: :obj:`typing.Optional[base.Integer]`

        :param close_date: Point in time (Unix timestamp) when the poll will be
            automatically closed. Must be at least 5 and no more than 600 seconds in
            the future. Can't be used together with open_period.
        :type close_date: :obj:`typing.Union[base.Integer, datetime.datetime,
            datetime.timedelta, None]`

        :param is_closed: Pass True, if the poll needs to be immediately closed
        :type is_closed: :obj:`typing.Optional[base.Boolean]`

        :param disable_notification: Sends the message silently. Users will receive
            a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object
            for an inline keyboard, custom reply keyboard, instructions to remove
            reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply,
            None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_poll(
            chat_id=self.chat.id,
            question=question,
            options=options,
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
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_sticker(
        self,
        sticker: typing.Union[base.InputFile, base.String],
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send .webp stickers.

        Source: https://core.telegram.org/bots/api#sendsticker

        :param sticker: Sticker to send.
        :type sticker: :obj:`typing.Union[base.InputFile, base.String]`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_sticker(
            chat_id=self.chat.id,
            sticker=sticker,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def reply_dice(
        self,
        emoji: typing.Optional[base.String] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup,
            ReplyKeyboardMarkup,
            ReplyKeyboardRemove,
            ForceReply,
            None,
        ] = None,
        reply: base.Boolean = True,
    ) -> Message:
        """
        Use this method to send an animated emoji that will display a random value.
        On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#senddice

        :param emoji: Emoji on which the dice throw animation is based. Currently,
            must be one of “🎲”, “🎯”, “🏀”, “⚽”, or “🎰”. Dice can have values 1-6
            for “🎲” and “🎯”, values 1-5 for “🏀” and “⚽”, and values 1-64 for “🎰”.
            Defaults to “🎲”
        :type emoji: :obj:`typing.Optional[base.String]`

        :param disable_notification: Sends the message silently. Users will receive
            a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :param allow_sending_without_reply: Pass True, if the message should be sent
            even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: Additional interface options. A JSON-serialized object
            for an inline keyboard, custom reply keyboard, instructions to remove
            reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply,
            None]`

        :param reply: fill 'reply_to_message_id'
        :type reply: :obj:`base.Boolean`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_dice(
            chat_id=self.chat.id,
            emoji=emoji,
            disable_notification=disable_notification,
            reply_to_message_id=self.message_id if reply else None,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
        )

    async def forward(
        self,
        chat_id: typing.Union[base.Integer, base.String],
        disable_notification: typing.Optional[base.Boolean] = None,
    ) -> Message:
        """
        Forward this message

        Source: https://core.telegram.org/bots/api#forwardmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        return await self.bot.forward_message(
            chat_id, self.chat.id, self.message_id, disable_notification
        )

    async def edit_text(
        self,
        text: base.String,
        parse_mode: typing.Optional[base.String] = None,
        entities: typing.Optional[typing.List[MessageEntity]] = None,
        disable_web_page_preview: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
    ) -> typing.Union[Message, base.Boolean]:
        """
        Use this method to edit text and game messages sent by the bot or via the bot (for inline bots).

        Source: https://core.telegram.org/bots/api#editmessagetext

        :param text: New text of the message
        :type text: :obj:`base.String`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param disable_web_page_preview: Disables link previews for links in this message
        :type disable_web_page_preview: :obj:`typing.Optional[base.Boolean]`

        :param reply_markup: A JSON-serialized object for an inline keyboard.
        :type reply_markup: :obj:`typing.Optional[types.InlineKeyboardMarkup]`

        :return: On success, if edited message is sent by the bot,
            the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        return await self.bot.edit_message_text(
            text=text,
            chat_id=self.chat.id,
            message_id=self.message_id,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup,
        )

    async def edit_caption(
        self,
        caption: base.String,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
    ) -> typing.Union[Message, base.Boolean]:
        """
        Use this method to edit captions of messages sent by the bot or via the bot
        (for inline bots).

        Source: https://core.telegram.org/bots/api#editmessagecaption

        :param caption: New caption of the message
        :type caption: :obj:`typing.Optional[base.String]`

        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show
            bold, italic, fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Optional[base.String]`

        :param caption_entities: List of special entities that appear in message text,
            which can be specified instead of parse_mode
        :type caption_entities: :obj:`typing.Optional[typing.List[MessageEntity]]`

        :param reply_markup: A JSON-serialized object for an inline keyboard
        :type reply_markup: :obj:`typing.Optional[types.InlineKeyboardMarkup]`

        :return: On success, if edited message is sent by the bot, the edited Message
            is returned, otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        return await self.bot.edit_message_caption(
            chat_id=self.chat.id,
            message_id=self.message_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            reply_markup=reply_markup,
        )

    async def edit_media(
        self,
        media: InputMedia,
        reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
    ) -> typing.Union[Message, base.Boolean]:
        """
        Use this method to edit audio, document, photo, or video messages.
        If a message is a part of a message album, then it can be edited only to a photo or a video.
        Otherwise, message type can be changed arbitrarily.
        When inline message is edited, new file can't be uploaded.
        Use previously uploaded file via its file_id or specify a URL.

        On success, if the edited message was sent by the bot,
        the edited Message is returned, otherwise True is returned.

        Source https://core.telegram.org/bots/api#editmessagemedia

        :param media: A JSON-serialized object for a new media content of the message
        :type media: :obj:`types.InputMedia`
        :param reply_markup: A JSON-serialized object for a new inline keyboard
        :type reply_markup: :obj:`typing.Optional[types.InlineKeyboardMarkup]`
        :return: On success, if the edited message was sent by the bot, the edited Message is returned,
            otherwise True is returned
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        return await self.bot.edit_message_media(
            media=media,
            chat_id=self.chat.id,
            message_id=self.message_id,
            reply_markup=reply_markup,
        )

    async def edit_reply_markup(
        self, reply_markup: typing.Optional[InlineKeyboardMarkup] = None
    ) -> typing.Union[Message, base.Boolean]:
        """
        Use this method to edit only the reply markup of messages sent by the bot or via the bot (for inline bots).

        Source: https://core.telegram.org/bots/api#editmessagereplymarkup

        :param reply_markup: A JSON-serialized object for an inline keyboard
        :type reply_markup: :obj:`typing.Optional[types.InlineKeyboardMarkup]`
        :return: On success, if edited message is sent by the bot, the edited Message is returned,
            otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        return await self.bot.edit_message_reply_markup(
            chat_id=self.chat.id, message_id=self.message_id, reply_markup=reply_markup
        )

    async def delete_reply_markup(self) -> typing.Union[Message, base.Boolean]:
        """
        Use this method to delete reply markup of messages sent by the bot or via the bot (for inline bots).

        :return: On success, if edited message is sent by the bot, the edited Message is returned,
            otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        return await self.bot.edit_message_reply_markup(
            chat_id=self.chat.id, message_id=self.message_id
        )

    async def edit_live_location(
        self,
        latitude: base.Float,
        longitude: base.Float,
        reply_markup: typing.Optional[InlineKeyboardMarkup] = None,
    ) -> typing.Union[Message, base.Boolean]:
        """
        Use this method to edit live location messages sent by the bot or via the bot (for inline bots).
        A location can be edited until its live_period expires or editing is explicitly disabled by a call
        to stopMessageLiveLocation.

        Source: https://core.telegram.org/bots/api#editmessagelivelocation

        :param latitude: Latitude of new location
        :type latitude: :obj:`base.Float`
        :param longitude: Longitude of new location
        :type longitude: :obj:`base.Float`
        :param reply_markup: A JSON-serialized object for a new inline keyboard.
        :type reply_markup: :obj:`typing.Optional[types.InlineKeyboardMarkup]`
        :return: On success, if the edited message was sent by the bot, the edited Message is returned,
            otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        return await self.bot.edit_message_live_location(
            latitude=latitude,
            longitude=longitude,
            chat_id=self.chat.id,
            message_id=self.message_id,
            reply_markup=reply_markup,
        )

    async def stop_live_location(
        self, reply_markup: typing.Optional[InlineKeyboardMarkup] = None
    ) -> typing.Union[Message, base.Boolean]:
        """
        Use this method to stop updating a live location message sent by the bot or via the bot
        (for inline bots) before live_period expires.

        Source: https://core.telegram.org/bots/api#stopmessagelivelocation

        :param reply_markup: A JSON-serialized object for a new inline keyboard.
        :type reply_markup: :obj:`typing.Optional[types.InlineKeyboardMarkup]`
        :return: On success, if the message was sent by the bot, the sent Message is returned,
            otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        return await self.bot.stop_message_live_location(
            chat_id=self.chat.id, message_id=self.message_id, reply_markup=reply_markup
        )

    async def delete(self) -> base.Boolean:
        """
        Use this method to delete a message, including service messages, with the following limitations:
        - A message can only be deleted if it was sent less than 48 hours ago.
        - Bots can delete outgoing messages in private chats, groups, and supergroups.
        - Bots can delete incoming messages in private chats.
        - Bots granted can_post_messages permissions can delete outgoing messages in channels.
        - If the bot is an administrator of a group, it can delete any message there.
        - If the bot has can_delete_messages permission in a supergroup or a channel, it can delete any message there.

        Source: https://core.telegram.org/bots/api#deletemessage

        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        return await self.bot.delete_message(self.chat.id, self.message_id)

    async def pin(
        self, disable_notification: typing.Optional[base.Boolean] = None,
    ) -> base.Boolean:
        """
        Use this method to add a message to the list of pinned messages in a chat.
        If the chat is not a private chat, the bot must be an administrator in the
        chat for this to work and must have the 'can_pin_messages' admin right in a
        supergroup or 'can_edit_messages' admin right in a channel. Returns True on
        success.

        Source: https://core.telegram.org/bots/api#pinchatmessage

        :param disable_notification: Pass True, if it is not necessary to send a
            notification to all group members about the new pinned message
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`

        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        return await self.chat.pin_message(self.message_id, disable_notification)

    async def unpin(self) -> base.Boolean:
        """
        Use this method to remove a message from the list of pinned messages in a
        chat. If the chat is not a private chat, the bot must be an administrator in
        the chat for this to work and must have the 'can_pin_messages' admin right in
        a supergroup or 'can_edit_messages' admin right in a channel. Returns True on
        success.

        Source: https://core.telegram.org/bots/api#unpinchatmessage

        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        return await self.chat.unpin_message(
            message_id=self.message_id,
        )

    async def send_copy(
        self: Message,
        chat_id: typing.Union[str, int],
        disable_notification: typing.Optional[bool] = None,
        disable_web_page_preview: typing.Optional[bool] = None,
        reply_to_message_id: typing.Optional[int] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[
            InlineKeyboardMarkup, ReplyKeyboardMarkup, None
        ] = None,
    ) -> Message:
        """
        Send copy of current message

        :param chat_id:
        :param disable_notification:
        :param disable_web_page_preview: for text messages only
        :param reply_to_message_id:
        :param allow_sending_without_reply:
        :param reply_markup:
        :return:
        """
        kwargs = {
            "chat_id": chat_id,
            "allow_sending_without_reply": allow_sending_without_reply,
            "reply_markup": reply_markup or self.reply_markup,
            "parse_mode": ParseMode.HTML,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
        }
        text = self.html_text if (self.text or self.caption) else None

        if self.text:
            kwargs["disable_web_page_preview"] = disable_web_page_preview
            return await self.bot.send_message(text=text, **kwargs)
        elif self.audio:
            return await self.bot.send_audio(
                audio=self.audio.file_id,
                caption=text,
                title=self.audio.title,
                performer=self.audio.performer,
                duration=self.audio.duration,
                **kwargs,
            )
        elif self.animation:
            return await self.bot.send_animation(
                animation=self.animation.file_id, caption=text, **kwargs
            )
        elif self.document:
            return await self.bot.send_document(
                document=self.document.file_id, caption=text, **kwargs
            )
        elif self.photo:
            return await self.bot.send_photo(
                photo=self.photo[-1].file_id, caption=text, **kwargs
            )
        elif self.sticker:
            kwargs.pop("parse_mode")
            return await self.bot.send_sticker(sticker=self.sticker.file_id, **kwargs)
        elif self.video:
            return await self.bot.send_video(
                video=self.video.file_id, caption=text, **kwargs
            )
        elif self.video_note:
            kwargs.pop("parse_mode")
            return await self.bot.send_video_note(
                video_note=self.video_note.file_id, **kwargs
            )
        elif self.voice:
            return await self.bot.send_voice(voice=self.voice.file_id, **kwargs)
        elif self.contact:
            kwargs.pop("parse_mode")
            return await self.bot.send_contact(
                phone_number=self.contact.phone_number,
                first_name=self.contact.first_name,
                last_name=self.contact.last_name,
                vcard=self.contact.vcard,
                **kwargs,
            )
        elif self.venue:
            kwargs.pop("parse_mode")
            return await self.bot.send_venue(
                latitude=self.venue.location.latitude,
                longitude=self.venue.location.longitude,
                title=self.venue.title,
                address=self.venue.address,
                foursquare_id=self.venue.foursquare_id,
                foursquare_type=self.venue.foursquare_type,
                **kwargs,
            )
        elif self.location:
            kwargs.pop("parse_mode")
            return await self.bot.send_location(
                latitude=self.location.latitude,
                longitude=self.location.longitude,
                **kwargs,
            )
        elif self.poll:
            kwargs.pop("parse_mode")
            return await self.bot.send_poll(
                question=self.poll.question,
                options=[option.text for option in self.poll.options],
                is_anonymous=self.poll.is_anonymous,
                allows_multiple_answers=self.poll.allows_multiple_answers
                **kwargs,
            )
        elif self.dice:
            kwargs.pop("parse_mode")
            return await self.bot.send_dice(
                emoji=self.dice.emoji,
                **kwargs,
            )
        else:
            raise TypeError("This type of message can't be copied.")

    async def copy_to(
        self,
        chat_id: typing.Union[base.Integer, base.String],
        caption: typing.Optional[base.String] = None,
        parse_mode: typing.Optional[base.String] = None,
        caption_entities: typing.Optional[typing.List[MessageEntity]] = None,
        disable_notification: typing.Optional[base.Boolean] = None,
        reply_to_message_id: typing.Optional[base.Integer] = None,
        allow_sending_without_reply: typing.Optional[base.Boolean] = None,
        reply_markup: typing.Union[InlineKeyboardMarkup,
                                   ReplyKeyboardMarkup,
                                   ReplyKeyboardRemove,
                                   ForceReply, None] = None,
    ) -> MessageId:
        return await self.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=self.chat.id,
            message_id=self.message_id,
            caption=caption,
            parse_mode=parse_mode,
            caption_entities=caption_entities,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup
        )

    def __int__(self):
        return self.message_id


class ContentType(helper.Helper):
    """
    List of message content types

    WARNING: Single elements

    :key: TEXT
    :key: AUDIO
    :key: DOCUMENT
    :key: GAME
    :key: PHOTO
    :key: STICKER
    :key: VIDEO
    :key: VIDEO_NOTE
    :key: VOICE
    :key: CONTACT
    :key: LOCATION
    :key: VENUE
    :key: POLL
    :key: DICE
    :key: NEW_CHAT_MEMBERS
    :key: LEFT_CHAT_MEMBER
    :key: INVOICE
    :key: SUCCESSFUL_PAYMENT
    :key: CONNECTED_WEBSITE
    :key: MIGRATE_TO_CHAT_ID
    :key: MIGRATE_FROM_CHAT_ID
    :key: UNKNOWN
    :key: ANY
    """

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
    POLL = helper.Item()  # poll
    DICE = helper.Item()  # dice
    NEW_CHAT_MEMBERS = helper.Item()  # new_chat_member
    LEFT_CHAT_MEMBER = helper.Item()  # left_chat_member
    INVOICE = helper.Item()  # invoice
    SUCCESSFUL_PAYMENT = helper.Item()  # successful_payment
    CONNECTED_WEBSITE = helper.Item()  # connected_website
    MESSAGE_AUTO_DELETE_TIMER_CHANGED = helper.Item()  # message_auto_delete_timer_changed
    MIGRATE_TO_CHAT_ID = helper.Item()  # migrate_to_chat_id
    MIGRATE_FROM_CHAT_ID = helper.Item()  # migrate_from_chat_id
    PINNED_MESSAGE = helper.Item()  # pinned_message
    NEW_CHAT_TITLE = helper.Item()  # new_chat_title
    NEW_CHAT_PHOTO = helper.Item()  # new_chat_photo
    DELETE_CHAT_PHOTO = helper.Item()  # delete_chat_photo
    GROUP_CHAT_CREATED = helper.Item()  # group_chat_created
    PASSPORT_DATA = helper.Item()  # passport_data
    PROXIMITY_ALERT_TRIGGERED = helper.Item()  # proximity_alert_triggered
    VOICE_CHAT_SCHEDULED = helper.Item() # voice_chat_scheduled
    VOICE_CHAT_STARTED = helper.Item() # voice_chat_started
    VOICE_CHAT_ENDED = helper.Item() # voice_chat_ended
    VOICE_CHAT_PARTICIPANTS_INVITED = helper.Item() # voice_chat_participants_invited

    UNKNOWN = helper.Item()  # unknown
    ANY = helper.Item()  # any


class ContentTypes(helper.Helper):
    """
    List of message content types

    WARNING: List elements.

    :key: TEXT
    :key: AUDIO
    :key: DOCUMENT
    :key: GAME
    :key: PHOTO
    :key: STICKER
    :key: VIDEO
    :key: VIDEO_NOTE
    :key: VOICE
    :key: CONTACT
    :key: LOCATION
    :key: VENUE
    :key: POLL
    :key: DICE
    :key: NEW_CHAT_MEMBERS
    :key: LEFT_CHAT_MEMBER
    :key: INVOICE
    :key: SUCCESSFUL_PAYMENT
    :key: CONNECTED_WEBSITE
    :key: MIGRATE_TO_CHAT_ID
    :key: MIGRATE_FROM_CHAT_ID
    :key: UNKNOWN
    :key: ANY
    """

    mode = helper.HelperMode.snake_case

    TEXT = helper.ListItem()  # text
    AUDIO = helper.ListItem()  # audio
    DOCUMENT = helper.ListItem()  # document
    ANIMATION = helper.ListItem()  # animation
    GAME = helper.ListItem()  # game
    PHOTO = helper.ListItem()  # photo
    STICKER = helper.ListItem()  # sticker
    VIDEO = helper.ListItem()  # video
    VIDEO_NOTE = helper.ListItem()  # video_note
    VOICE = helper.ListItem()  # voice
    CONTACT = helper.ListItem()  # contact
    LOCATION = helper.ListItem()  # location
    VENUE = helper.ListItem()  # venue
    POLL = helper.ListItem()  # poll
    DICE = helper.ListItem()  # dice
    NEW_CHAT_MEMBERS = helper.ListItem()  # new_chat_member
    LEFT_CHAT_MEMBER = helper.ListItem()  # left_chat_member
    INVOICE = helper.ListItem()  # invoice
    SUCCESSFUL_PAYMENT = helper.ListItem()  # successful_payment
    CONNECTED_WEBSITE = helper.ListItem()  # connected_website
    MIGRATE_TO_CHAT_ID = helper.ListItem()  # migrate_to_chat_id
    MIGRATE_FROM_CHAT_ID = helper.ListItem()  # migrate_from_chat_id
    PINNED_MESSAGE = helper.ListItem()  # pinned_message
    NEW_CHAT_TITLE = helper.ListItem()  # new_chat_title
    NEW_CHAT_PHOTO = helper.ListItem()  # new_chat_photo
    DELETE_CHAT_PHOTO = helper.ListItem()  # delete_chat_photo
    GROUP_CHAT_CREATED = helper.ListItem()  # group_chat_created
    PASSPORT_DATA = helper.ListItem()  # passport_data

    UNKNOWN = helper.ListItem()  # unknown
    ANY = helper.ListItem()  # any


class ParseMode(helper.Helper):
    """
    Parse modes

    :key: MARKDOWN
    :key: HTML
    """

    mode = helper.HelperMode.lowercase

    MARKDOWN = helper.Item()
    MARKDOWN_V2 = helper.Item()
    HTML = helper.Item()
