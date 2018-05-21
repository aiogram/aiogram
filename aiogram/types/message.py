import datetime
import functools
import typing

from . import base
from . import fields
from .audio import Audio
from .chat import Chat
from .contact import Contact
from .document import Document
from .game import Game
from .invoice import Invoice
from .location import Location
from .message_entity import MessageEntity
from .photo_size import PhotoSize
from .sticker import Sticker
from .successful_payment import SuccessfulPayment
from .user import User
from .venue import Venue
from .video import Video
from .video_note import VideoNote
from .voice import Voice
from ..utils import helper


class Message(base.TelegramObject):
    """
    This object represents a message.

    https://core.telegram.org/bots/api#message
    """
    message_id: base.Integer = fields.Field()
    from_user: User = fields.Field(alias='from', base=User)
    date: datetime.datetime = fields.DateTimeField()
    chat: Chat = fields.Field(base=Chat)
    forward_from: User = fields.Field(base=User)
    forward_from_chat: Chat = fields.Field(base=Chat)
    forward_from_message_id: base.Integer = fields.Field()
    forward_signature: base.String = fields.Field()
    forward_date: base.Integer = fields.Field()
    reply_to_message: 'Message' = fields.Field(base='Message')
    edit_date: base.Integer = fields.Field()
    media_group_id: base.String = fields.Field()
    author_signature: base.String = fields.Field()
    text: base.String = fields.Field()
    entities: typing.List[MessageEntity] = fields.ListField(base=MessageEntity)
    caption_entities: typing.List[MessageEntity] = fields.ListField(base=MessageEntity)
    audio: Audio = fields.Field(base=Audio)
    document: Document = fields.Field(base=Document)
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
    new_chat_members: typing.List[User] = fields.ListField(base=User)
    left_chat_member: User = fields.Field(base=User)
    new_chat_title: base.String = fields.Field()
    new_chat_photo: typing.List[PhotoSize] = fields.ListField(base=PhotoSize)
    delete_chat_photo: base.Boolean = fields.Field()
    group_chat_created: base.Boolean = fields.Field()
    supergroup_chat_created: base.Boolean = fields.Field()
    channel_chat_created: base.Boolean = fields.Field()
    migrate_to_chat_id: base.Integer = fields.Field()
    migrate_from_chat_id: base.Integer = fields.Field()
    pinned_message: 'Message' = fields.Field(base='Message')
    invoice: Invoice = fields.Field(base=Invoice)
    successful_payment: SuccessfulPayment = fields.Field(base=SuccessfulPayment)
    connected_website: base.String = fields.Field()

    @property
    @functools.lru_cache()
    def content_type(self):
        if self.text:
            return ContentType.TEXT[0]
        if self.audio:
            return ContentType.AUDIO[0]
        if self.document:
            return ContentType.DOCUMENT[0]
        if self.game:
            return ContentType.GAME[0]
        if self.photo:
            return ContentType.PHOTO[0]
        if self.sticker:
            return ContentType.STICKER[0]
        if self.video:
            return ContentType.VIDEO[0]
        if self.video_note:
            return ContentType.VIDEO_NOTE[0]
        if self.voice:
            return ContentType.VOICE[0]
        if self.contact:
            return ContentType.CONTACT[0]
        if self.venue:
            return ContentType.VENUE[0]
        if self.location:
            return ContentType.LOCATION[0]
        if self.new_chat_members:
            return ContentType.NEW_CHAT_MEMBERS[0]
        if self.left_chat_member:
            return ContentType.LEFT_CHAT_MEMBER[0]
        if self.invoice:
            return ContentType.INVOICE[0]
        if self.successful_payment:
            return ContentType.SUCCESSFUL_PAYMENT[0]
        if self.connected_website:
            return ContentType.CONNECTED_WEBSITE[0]
        if self.migrate_from_chat_id:
            return ContentType.MIGRATE_FROM_CHAT_ID[0]
        if self.migrate_to_chat_id:
            return ContentType.MIGRATE_TO_CHAT_ID[0]
        else:
            return ContentType.UNKNOWN[0]

    def is_command(self):
        """
        Check message text is command

        :return: bool
        """
        return self.text and self.text.startswith('/')

    def get_full_command(self):
        """
        Split command and args

        :return: tuple of (command, args)
        """
        if self.is_command():
            command, _, args = self.text.partition(' ')
            return command, args

    def get_command(self, pure=False):
        """
        Get command from message

        :return:
        """
        command = self.get_full_command()
        if command:
            command = command[0]
            if pure:
                command, _, _ = command[1:].partition('@')
            return command

    def get_args(self):
        """
        Get arguments

        :return:
        """
        command = self.get_full_command()
        if command:
            return command[1].strip()

    @property
    def md_text(self) -> str:
        """
        Text or caption formatted as markdown.

        :return: str
        """
        text = self.caption if self.caption else self.text

        if self.text and self.entities:
            for entity in reversed(self.entities):
                text = entity.apply_md(text)

        return text

    @property
    def html_text(self) -> str:
        """
        Text or caption formatted as HTML.

        :return: str
        """
        text = self.caption if self.caption else self.text

        if self.text and self.entities:
            for entity in reversed(self.entities):
                text = entity.apply_html(text)

        return text

    async def reply(self, text, parse_mode=None, disable_web_page_preview=None,
                    disable_notification=None, reply_markup=None, reply=True) -> 'Message':
        """
        Reply to this message

        :param text: str
        :param parse_mode: str
        :param disable_web_page_preview: bool
        :param disable_notification: bool
        :param reply_markup:
        :param reply: fill 'reply_to_message_id'
        :return: :class:`aiogram.types.Message`
        """
        return await self.bot.send_message(chat_id=self.chat.id, text=text,
                                           parse_mode=parse_mode,
                                           disable_web_page_preview=disable_web_page_preview,
                                           disable_notification=disable_notification,
                                           reply_to_message_id=self.message_id if reply else None,
                                           reply_markup=reply_markup)

    async def reply_photo(self, photo: typing.Union[base.InputFile, base.String],
                          caption: typing.Union[base.String, None] = None,
                          disable_notification: typing.Union[base.Boolean, None] = None,
                          reply_markup=None, reply=True) -> 'Message':
        """
        Use this method to send photos.

        Source: https://core.telegram.org/bots/api#sendphoto

        :param photo: Photo to send.
        :type photo: :obj:`typing.Union[base.InputFile, base.String]`
        :param caption: Photo caption (may also be used when resending photos by file_id), 0-200 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: Additional interface options.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_photo(chat_id=self.chat.id, photo=photo, caption=caption,
                                         disable_notification=disable_notification,
                                         reply_to_message_id=self.message_id if reply else None,
                                         reply_markup=reply_markup)

    async def reply_audio(self, audio: typing.Union[base.InputFile, base.String],
                          caption: typing.Union[base.String, None] = None,
                          duration: typing.Union[base.Integer, None] = None,
                          performer: typing.Union[base.String, None] = None,
                          title: typing.Union[base.String, None] = None,
                          disable_notification: typing.Union[base.Boolean, None] = None,
                          reply_markup=None,
                          reply=True) -> 'Message':
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player.
        Your audio must be in the .mp3 format.

        For sending voice messages, use the sendVoice method instead.

        Source: https://core.telegram.org/bots/api#sendaudio

        :param audio: Audio file to send.
        :type audio: :obj:`typing.Union[base.InputFile, base.String]`
        :param caption: Audio caption, 0-200 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param duration: Duration of the audio in seconds
        :type duration: :obj:`typing.Union[base.Integer, None]`
        :param performer: Performer
        :type performer: :obj:`typing.Union[base.String, None]`
        :param title: Track name
        :type title: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: Additional interface options.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_audio(chat_id=self.chat.id,
                                         audio=audio,
                                         caption=caption,
                                         duration=duration,
                                         performer=performer,
                                         title=title,
                                         disable_notification=disable_notification,
                                         reply_to_message_id=self.message_id if reply else None,
                                         reply_markup=reply_markup)

    async def reply_document(self, document: typing.Union[base.InputFile, base.String],
                             caption: typing.Union[base.String, None] = None,
                             disable_notification: typing.Union[base.Boolean, None] = None,
                             reply_markup=None,
                             reply=True) -> 'Message':
        """
        Use this method to send general files.

        Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#senddocument

        :param document: File to send.
        :type document: :obj:`typing.Union[base.InputFile, base.String]`
        :param caption: Document caption (may also be used when resending documents by file_id), 0-200 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: Additional interface options.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply], None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_document(chat_id=self.chat.id,
                                            document=document,
                                            caption=caption,
                                            disable_notification=disable_notification,
                                            reply_to_message_id=self.message_id if reply else None,
                                            reply_markup=reply_markup)

    async def reply_video(self, video: typing.Union[base.InputFile, base.String],
                          duration: typing.Union[base.Integer, None] = None,
                          width: typing.Union[base.Integer, None] = None,
                          height: typing.Union[base.Integer, None] = None,
                          caption: typing.Union[base.String, None] = None,
                          disable_notification: typing.Union[base.Boolean, None] = None,
                          reply_markup=None,
                          reply=True) -> 'Message':
        """
        Use this method to send video files, Telegram clients support mp4 videos
        (other formats may be sent as Document).

        Source: https://core.telegram.org/bots/api#sendvideo

        :param video: Video to send.
        :type video: :obj:`typing.Union[base.InputFile, base.String]`
        :param duration: Duration of sent video in seconds
        :type duration: :obj:`typing.Union[base.Integer, None]`
        :param width: Video width
        :type width: :obj:`typing.Union[base.Integer, None]`
        :param height: Video height
        :type height: :obj:`typing.Union[base.Integer, None]`
        :param caption: Video caption (may also be used when resending videos by file_id), 0-200 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: Additional interface options.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_video(chat_id=self.chat.id,
                                         video=video,
                                         duration=duration,
                                         width=width,
                                         height=height,
                                         caption=caption,
                                         disable_notification=disable_notification,
                                         reply_to_message_id=self.message_id if reply else None,
                                         reply_markup=reply_markup)

    async def reply_voice(self, voice: typing.Union[base.InputFile, base.String],
                          caption: typing.Union[base.String, None] = None,
                          duration: typing.Union[base.Integer, None] = None,
                          disable_notification: typing.Union[base.Boolean, None] = None,
                          reply_markup=None,
                          reply=True) -> 'Message':
        """
        Use this method to send audio files, if you want Telegram clients to display the file
        as a playable voice message.

        For this to work, your audio must be in an .ogg file encoded with OPUS
        (other formats may be sent as Audio or Document).

        Source: https://core.telegram.org/bots/api#sendvoice

        :param voice: Audio file to send.
        :type voice: :obj:`typing.Union[base.InputFile, base.String]`
        :param caption: Voice message caption, 0-200 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param duration: Duration of the voice message in seconds
        :type duration: :obj:`typing.Union[base.Integer, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: Additional interface options.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_voice(chat_id=self.chat.id,
                                         voice=voice,
                                         caption=caption,
                                         duration=duration,
                                         disable_notification=disable_notification,
                                         reply_to_message_id=self.message_id if reply else None,
                                         reply_markup=reply_markup)

    async def reply_video_note(self, video_note: typing.Union[base.InputFile, base.String],
                               duration: typing.Union[base.Integer, None] = None,
                               length: typing.Union[base.Integer, None] = None,
                               disable_notification: typing.Union[base.Boolean, None] = None,
                               reply_markup=None,
                               reply=True) -> 'Message':
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long.
        Use this method to send video messages.

        Source: https://core.telegram.org/bots/api#sendvideonote

        :param video_note: Video note to send.
        :type video_note: :obj:`typing.Union[base.InputFile, base.String]`
        :param duration: Duration of sent video in seconds
        :type duration: :obj:`typing.Union[base.Integer, None]`
        :param length: Video width and height
        :type length: :obj:`typing.Union[base.Integer, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: Additional interface options.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_video_note(chat_id=self.chat.id,
                                              video_note=video_note,
                                              duration=duration,
                                              length=length,
                                              disable_notification=disable_notification,
                                              reply_to_message_id=self.message_id if reply else None,
                                              reply_markup=reply_markup)

    async def reply_media_group(self, media: typing.Union['MediaGroup', typing.List],
                                disable_notification: typing.Union[base.Boolean, None] = None,
                                reply=True) -> typing.List['Message']:
        """
        Use this method to send a group of photos or videos as an album.

        Source: https://core.telegram.org/bots/api#sendmediagroup

        :param media: A JSON-serialized array describing photos and videos to be sent
        :type media: :obj:`typing.Union[types.MediaGroup, typing.List]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, an array of the sent Messages is returned.
        :rtype: typing.List[types.Message]
        """
        return await self.bot.send_media_group(self.chat.id,
                                               media=media,
                                               disable_notification=disable_notification,
                                               reply_to_message_id=self.message_id if reply else None)

    async def reply_location(self, latitude: base.Float,
                             longitude: base.Float, live_period: typing.Union[base.Integer, None] = None,
                             disable_notification: typing.Union[base.Boolean, None] = None,
                             reply_markup=None,
                             reply=True) -> 'Message':
        """
        Use this method to send point on the map.

        Source: https://core.telegram.org/bots/api#sendlocation

        :param latitude: Latitude of the location
        :type latitude: :obj:`base.Float`
        :param longitude: Longitude of the location
        :type longitude: :obj:`base.Float`
        :param live_period: Period in seconds for which the location will be updated
        :type live_period: :obj:`typing.Union[base.Integer, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: Additional interface options.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_location(chat_id=self.chat.id,
                                            latitude=latitude,
                                            longitude=longitude,
                                            live_period=live_period,
                                            disable_notification=disable_notification,
                                            reply_to_message_id=self.message_id if reply else None,
                                            reply_markup=reply_markup)

    async def edit_live_location(self, latitude: base.Float, longitude: base.Float,
                                 reply_markup=None) -> 'Message' or base.Boolean:
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
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, if the edited message was sent by the bot, the edited Message is returned,
            otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        return await self.bot.edit_message_live_location(latitude=latitude, longitude=longitude,
                                                         chat_id=self.chat.id, message_id=self.message_id,
                                                         reply_markup=reply_markup)

    async def stop_live_location(self, reply_markup=None) -> 'Message' or base.Boolean:
        """
        Use this method to stop updating a live location message sent by the bot or via the bot
        (for inline bots) before live_period expires.

        Source: https://core.telegram.org/bots/api#stopmessagelivelocation

        :param reply_markup: A JSON-serialized object for a new inline keyboard.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, if the message was sent by the bot, the sent Message is returned,
            otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        return await self.bot.stop_message_live_location(chat_id=self.chat.id, message_id=self.message_id,
                                                         reply_markup=reply_markup)

    async def send_venue(self, latitude: base.Float, longitude: base.Float, title: base.String, address: base.String,
                         foursquare_id: typing.Union[base.String, None] = None,
                         disable_notification: typing.Union[base.Boolean, None] = None,
                         reply_markup=None,
                         reply=True) -> 'Message':
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
        :type foursquare_id: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: Additional interface options.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_venue(chat_id=self.chat.id,
                                         latitude=latitude,
                                         longitude=longitude,
                                         title=title,
                                         address=address,
                                         foursquare_id=foursquare_id,
                                         disable_notification=disable_notification,
                                         reply_to_message_id=self.message_id if reply else None,
                                         reply_markup=reply_markup)

    async def send_contact(self, phone_number: base.String,
                           first_name: base.String, last_name: typing.Union[base.String, None] = None,
                           disable_notification: typing.Union[base.Boolean, None] = None,
                           reply_markup=None,
                           reply=True) -> 'Message':
        """
        Use this method to send phone contacts.

        Source: https://core.telegram.org/bots/api#sendcontact

        :param phone_number: Contact's phone number
        :type phone_number: :obj:`base.String`
        :param first_name: Contact's first name
        :type first_name: :obj:`base.String`
        :param last_name: Contact's last name
        :type last_name: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: Additional interface options.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_contact(chat_id=self.chat.id,
                                           phone_number=phone_number,
                                           first_name=first_name, last_name=last_name,
                                           disable_notification=disable_notification,
                                           reply_to_message_id=self.message_id if reply else None,
                                           reply_markup=reply_markup)

    async def forward(self, chat_id, disable_notification=None) -> 'Message':
        """
        Forward this message

        :param chat_id:
        :param disable_notification:
        :return:
        """
        return await self.bot.forward_message(chat_id, self.chat.id, self.message_id, disable_notification)

    async def edit_text(self, text: base.String,
                        parse_mode: typing.Union[base.String, None] = None,
                        disable_web_page_preview: typing.Union[base.Boolean, None] = None,
                        reply_markup=None):
        """
        Use this method to edit text and game messages sent by the bot or via the bot (for inline bots).

        Source: https://core.telegram.org/bots/api#editmessagetext

        :param text: New text of the message
        :type text: :obj:`base.String`
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Union[base.String, None]`
        :param disable_web_page_preview: Disables link previews for links in this message
        :type disable_web_page_preview: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: A JSON-serialized object for an inline keyboard.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, if edited message is sent by the bot,
            the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        return await self.bot.edit_message_text(text=text,
                                                chat_id=self.chat.id, message_id=self.message_id,
                                                parse_mode=parse_mode,
                                                disable_web_page_preview=disable_web_page_preview,
                                                reply_markup=reply_markup)

    async def delete(self):
        """
        Delete this message

        :return: bool
        """
        return await self.bot.delete_message(self.chat.id, self.message_id)

    async def reply_sticker(self, sticker: typing.Union[base.InputFile, base.String],
                            disable_notification: typing.Union[base.Boolean, None] = None,
                            reply_markup=None, reply=True) -> 'Message':
        """
        Use this method to send .webp stickers.

        Source: https://core.telegram.org/bots/api#sendsticker

        :param sticker: Sticker to send.
        :type sticker: :obj:`typing.Union[base.InputFile, base.String]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: Additional interface options.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :param reply: fill 'reply_to_message_id'
        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        return await self.bot.send_sticker(chat_id=self.chat.id, sticker=sticker,
                                           disable_notification=disable_notification,
                                           reply_to_message_id=self.message_id if reply else None,
                                           reply_markup=reply_markup)

    async def pin(self, disable_notification: bool = False):
        """
        Pin message

        :param disable_notification:
        :return:
        """
        return await self.chat.pin_message(self.message_id, disable_notification)

    def __int__(self):
        return self.message_id


class ContentType(helper.Helper):
    """
    List of message content types

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
    GAME = helper.ListItem()  # game
    PHOTO = helper.ListItem()  # photo
    STICKER = helper.ListItem()  # sticker
    VIDEO = helper.ListItem()  # video
    VIDEO_NOTE = helper.ListItem()  # video_note
    VOICE = helper.ListItem()  # voice
    CONTACT = helper.ListItem()  # contact
    LOCATION = helper.ListItem()  # location
    VENUE = helper.ListItem()  # venue
    NEW_CHAT_MEMBERS = helper.ListItem()  # new_chat_member
    LEFT_CHAT_MEMBER = helper.ListItem()  # left_chat_member
    INVOICE = helper.ListItem()  # invoice
    SUCCESSFUL_PAYMENT = helper.ListItem()  # successful_payment
    CONNECTED_WEBSITE = helper.ListItem()  # connected_website
    MIGRATE_TO_CHAT_ID = helper.ListItem()  # migrate_to_chat_id
    MIGRATE_FROM_CHAT_ID = helper.ListItem()  # migrate_from_chat_id

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
    HTML = helper.Item()
