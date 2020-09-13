from __future__ import annotations

import datetime
import typing
import warnings

from .base import BaseBot, api
from .. import types
from ..types import base
from ..utils.mixins import DataMixin, ContextInstanceMixin
from ..utils.payload import generate_payload, prepare_arg, prepare_attachment, prepare_file


class Bot(BaseBot, DataMixin, ContextInstanceMixin):
    """
    Base bot class
    """

    @property
    async def me(self) -> types.User:
        """
        Alias for self.get_me() but lazy and with caching.

        :return: :class:`aiogram.types.User`
        """
        if not hasattr(self, '_me'):
            setattr(self, '_me', await self.get_me())
        return getattr(self, '_me')

    @me.deleter
    def me(self):
        """
        Reset `me`

        .. code-block:: python3

            await bot.me

        :return: :obj:`aiogram.types.User`
        """
        if hasattr(self, '_me'):
            delattr(self, '_me')

    async def download_file_by_id(self, file_id: base.String, destination=None,
                                  timeout: base.Integer = 30, chunk_size: base.Integer = 65536,
                                  seek: base.Boolean = True):
        """
        Download file by file_id to destination

        if You want to automatically create destination (:class:`io.BytesIO`) use default
        value of destination and handle result of this method.

        :param file_id: str
        :param destination: filename or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO`
        :param timeout: int
        :param chunk_size: int
        :param seek: bool - go to start of file when downloading is finished
        :return: destination
        """
        file = await self.get_file(file_id)
        return await self.download_file(file_path=file.file_path, destination=destination,
                                        timeout=timeout, chunk_size=chunk_size, seek=seek)

    # === Getting updates ===
    # https://core.telegram.org/bots/api#getting-updates

    async def get_updates(self, offset: typing.Union[base.Integer, None] = None,
                          limit: typing.Union[base.Integer, None] = None,
                          timeout: typing.Union[base.Integer, None] = None,
                          allowed_updates:
                          typing.Union[typing.List[base.String], None] = None) -> typing.List[types.Update]:
        """
        Use this method to receive incoming updates using long polling (wiki).

        Notes
        1. This method will not work if an outgoing webhook is set up.
        2. In order to avoid getting duplicate updates, recalculate offset after each server response.

        Source: https://core.telegram.org/bots/api#getupdates

        :param offset: Identifier of the first update to be returned
        :type offset: :obj:`typing.Union[base.Integer, None]`
        :param limit: Limits the number of updates to be retrieved
        :type limit: :obj:`typing.Union[base.Integer, None]`
        :param timeout: Timeout in seconds for long polling
        :type timeout: :obj:`typing.Union[base.Integer, None]`
        :param allowed_updates: List the types of updates you want your bot to receive
        :type allowed_updates: :obj:`typing.Union[typing.List[base.String], None]`
        :return: An Array of Update objects is returned
        :rtype: :obj:`typing.List[types.Update]`
        """
        allowed_updates = prepare_arg(allowed_updates)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_UPDATES, payload)
        return [types.Update(**update) for update in result]

    async def set_webhook(self, url: base.String,
                          certificate: typing.Union[base.InputFile, None] = None,
                          max_connections: typing.Union[base.Integer, None] = None,
                          allowed_updates: typing.Union[typing.List[base.String], None] = None) -> base.Boolean:
        """
        Use this method to specify a url and receive incoming updates via an outgoing webhook.
        Whenever there is an update for the bot, we will send an HTTPS POST request to the specified url,
        containing a JSON-serialized Update. In case of an unsuccessful request,
        we will give up after a reasonable amount of attempts.

        Source: https://core.telegram.org/bots/api#setwebhook

        :param url: HTTPS url to send updates to. Use an empty string to remove webhook integration
        :type url: :obj:`base.String`
        :param certificate: Upload your public key certificate so that the root certificate in use can be checked
        :type certificate: :obj:`typing.Union[base.InputFile, None]`
        :param max_connections: Maximum allowed number of simultaneous HTTPS connections to the webhook
            for update delivery, 1-100.
        :type max_connections: :obj:`typing.Union[base.Integer, None]`
        :param allowed_updates: List the types of updates you want your bot to receive
        :type allowed_updates: :obj:`typing.Union[typing.List[base.String], None]`
        :return: Returns true
        :rtype: :obj:`base.Boolean`
        """
        allowed_updates = prepare_arg(allowed_updates)
        payload = generate_payload(**locals(), exclude=['certificate'])

        files = {}
        prepare_file(payload, files, 'certificate', certificate)

        result = await self.request(api.Methods.SET_WEBHOOK, payload, files)
        return result

    async def delete_webhook(self) -> base.Boolean:
        """
        Use this method to remove webhook integration if you decide to switch back to getUpdates.
        Returns True on success. Requires no parameters.

        Source: https://core.telegram.org/bots/api#deletewebhook

        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.DELETE_WEBHOOK, payload)
        return result

    async def get_webhook_info(self) -> types.WebhookInfo:
        """
        Use this method to get current webhook status. Requires no parameters.

        If the bot is using getUpdates, will return an object with the url field empty.

        Source: https://core.telegram.org/bots/api#getwebhookinfo

        :return: On success, returns a WebhookInfo object
        :rtype: :obj:`types.WebhookInfo`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_WEBHOOK_INFO, payload)
        return types.WebhookInfo(**result)

    # === Base methods ===
    # https://core.telegram.org/bots/api#available-methods

    async def get_me(self) -> types.User:
        """
        A simple method for testing your bot's auth token. Requires no parameters.

        Source: https://core.telegram.org/bots/api#getme

        :return: Returns basic information about the bot in form of a User object
        :rtype: :obj:`types.User`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_ME, payload)
        return types.User(**result)

    async def send_message(self, chat_id: typing.Union[base.Integer, base.String], text: base.String,
                           parse_mode: typing.Union[base.String, None] = None,
                           disable_web_page_preview: typing.Union[base.Boolean, None] = None,
                           disable_notification: typing.Union[base.Boolean, None] = None,
                           reply_to_message_id: typing.Union[base.Integer, None] = None,
                           reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                      types.ReplyKeyboardMarkup,
                                                      types.ReplyKeyboardRemove,
                                                      types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send text messages.

        Source: https://core.telegram.org/bots/api#sendmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param text: Text of the message to be sent
        :type text: :obj:`base.String`
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Union[base.String, None]`
        :param disable_web_page_preview: Disables link previews for links in this message
        :type disable_web_page_preview: :obj:`typing.Union[base.Boolean, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """

        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())
        if self.parse_mode:
            payload.setdefault('parse_mode', self.parse_mode)

        result = await self.request(api.Methods.SEND_MESSAGE, payload)
        return types.Message(**result)

    async def forward_message(self, chat_id: typing.Union[base.Integer, base.String],
                              from_chat_id: typing.Union[base.Integer, base.String], message_id: base.Integer,
                              disable_notification: typing.Union[base.Boolean, None] = None) -> types.Message:
        """
        Use this method to forward messages of any kind.

        Source: https://core.telegram.org/bots/api#forwardmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param from_chat_id: Unique identifier for the chat where the original message was sent
        :type from_chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param message_id: Message identifier in the chat specified in from_chat_id
        :type message_id: :obj:`base.Integer`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.FORWARD_MESSAGE, payload)
        return types.Message(**result)

    async def send_photo(self, chat_id: typing.Union[base.Integer, base.String],
                         photo: typing.Union[base.InputFile, base.String],
                         caption: typing.Union[base.String, None] = None,
                         parse_mode: typing.Union[base.String, None] = None,
                         disable_notification: typing.Union[base.Boolean, None] = None,
                         reply_to_message_id: typing.Union[base.Integer, None] = None,
                         reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                    types.ReplyKeyboardMarkup,
                                                    types.ReplyKeyboardRemove,
                                                    types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send photos.

        Source: https://core.telegram.org/bots/api#sendphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param photo: Photo to send
        :type photo: :obj:`typing.Union[base.InputFile, base.String]`
        :param caption: Photo caption (may also be used when resending photos by file_id), 0-1024 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['photo'])
        if self.parse_mode:
            payload.setdefault('parse_mode', self.parse_mode)

        files = {}
        prepare_file(payload, files, 'photo', photo)

        result = await self.request(api.Methods.SEND_PHOTO, payload, files)
        return types.Message(**result)

    async def send_audio(self, chat_id: typing.Union[base.Integer, base.String],
                         audio: typing.Union[base.InputFile, base.String],
                         caption: typing.Union[base.String, None] = None,
                         parse_mode: typing.Union[base.String, None] = None,
                         duration: typing.Union[base.Integer, None] = None,
                         performer: typing.Union[base.String, None] = None,
                         title: typing.Union[base.String, None] = None,
                         thumb: typing.Union[base.InputFile, base.String, None] = None,
                         disable_notification: typing.Union[base.Boolean, None] = None,
                         reply_to_message_id: typing.Union[base.Integer, None] = None,
                         reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                    types.ReplyKeyboardMarkup,
                                                    types.ReplyKeyboardRemove,
                                                    types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player.
        Your audio must be in the .mp3 format.

        For sending voice messages, use the sendVoice method instead.

        Source: https://core.telegram.org/bots/api#sendaudio

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param audio: Audio file to send
        :type audio: :obj:`typing.Union[base.InputFile, base.String]`
        :param caption: Audio caption, 0-1024 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Union[base.String, None]`
        :param duration: Duration of the audio in seconds
        :type duration: :obj:`typing.Union[base.Integer, None]`
        :param performer: Performer
        :type performer: :obj:`typing.Union[base.String, None]`
        :param title: Track name
        :type title: :obj:`typing.Union[base.String, None]`
        :param thumb: Thumbnail of the file sent
        :type thumb: :obj:`typing.Union[base.InputFile, base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup,
            types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['audio', 'thumb'])
        if self.parse_mode:
            payload.setdefault('parse_mode', self.parse_mode)

        files = {}
        prepare_file(payload, files, 'audio', audio)
        prepare_attachment(payload, files, 'thumb', thumb)

        result = await self.request(api.Methods.SEND_AUDIO, payload, files)
        return types.Message(**result)

    async def send_document(self, chat_id: typing.Union[base.Integer, base.String],
                            document: typing.Union[base.InputFile, base.String],
                            thumb: typing.Union[base.InputFile, base.String, None] = None,
                            caption: typing.Union[base.String, None] = None,
                            parse_mode: typing.Union[base.String, None] = None,
                            disable_notification: typing.Union[base.Boolean, None] = None,
                            reply_to_message_id: typing.Union[base.Integer, None] = None,
                            reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                       types.ReplyKeyboardMarkup,
                                                       types.ReplyKeyboardRemove,
                                                       types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send general files.

        Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#senddocument

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param document: File to send
        :type document: :obj:`typing.Union[base.InputFile, base.String]`
        :param thumb: Thumbnail of the file sent
        :type thumb: :obj:`typing.Union[base.InputFile, base.String, None]`
        :param caption: Document caption (may also be used when resending documents by file_id), 0-1024 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup,
            types.ReplyKeyboardRemove, types.ForceReply], None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['document'])
        if self.parse_mode:
            payload.setdefault('parse_mode', self.parse_mode)

        files = {}
        prepare_file(payload, files, 'document', document)
        prepare_attachment(payload, files, 'thumb', thumb)

        result = await self.request(api.Methods.SEND_DOCUMENT, payload, files)
        return types.Message(**result)

    async def send_video(self, chat_id: typing.Union[base.Integer, base.String],
                         video: typing.Union[base.InputFile, base.String],
                         duration: typing.Union[base.Integer, None] = None,
                         width: typing.Union[base.Integer, None] = None,
                         height: typing.Union[base.Integer, None] = None,
                         thumb: typing.Union[base.InputFile, base.String, None] = None,
                         caption: typing.Union[base.String, None] = None,
                         parse_mode: typing.Union[base.String, None] = None,
                         supports_streaming: typing.Union[base.Boolean, None] = None,
                         disable_notification: typing.Union[base.Boolean, None] = None,
                         reply_to_message_id: typing.Union[base.Integer, None] = None,
                         reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                    types.ReplyKeyboardMarkup,
                                                    types.ReplyKeyboardRemove,
                                                    types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send video files, Telegram clients support mp4 videos
        (other formats may be sent as Document).

        Source: https://core.telegram.org/bots/api#sendvideo

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param video: Video to send
        :type video: :obj:`typing.Union[base.InputFile, base.String]`
        :param duration: Duration of sent video in seconds
        :type duration: :obj:`typing.Union[base.Integer, None]`
        :param width: Video width
        :type width: :obj:`typing.Union[base.Integer, None]`
        :param height: Video height
        :type height: :obj:`typing.Union[base.Integer, None]`
        :param thumb: Thumbnail of the file sent
        :type thumb: :obj:`typing.Union[base.InputFile, base.String, None]`
        :param caption: Video caption (may also be used when resending videos by file_id), 0-1024 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Union[base.String, None]`
        :param supports_streaming: Pass True, if the uploaded video is suitable for streaming
        :type supports_streaming: :obj:`typing.Union[base.Boolean, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['video', 'thumb'])
        if self.parse_mode:
            payload.setdefault('parse_mode', self.parse_mode)

        files = {}
        prepare_file(payload, files, 'video', video)
        prepare_attachment(payload, files, 'thumb', thumb)

        result = await self.request(api.Methods.SEND_VIDEO, payload, files)
        return types.Message(**result)

    async def send_animation(self,
                             chat_id: typing.Union[base.Integer, base.String],
                             animation: typing.Union[base.InputFile, base.String],
                             duration: typing.Union[base.Integer, None] = None,
                             width: typing.Union[base.Integer, None] = None,
                             height: typing.Union[base.Integer, None] = None,
                             thumb: typing.Union[typing.Union[base.InputFile, base.String], None] = None,
                             caption: typing.Union[base.String, None] = None,
                             parse_mode: typing.Union[base.String, None] = None,
                             disable_notification: typing.Union[base.Boolean, None] = None,
                             reply_to_message_id: typing.Union[base.Integer, None] = None,
                             reply_markup: typing.Union[typing.Union[types.InlineKeyboardMarkup,
                                                                     types.ReplyKeyboardMarkup,
                                                                     types.ReplyKeyboardRemove,
                                                                     types.ForceReply], None] = None
                             ) -> types.Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound).

        On success, the sent Message is returned.
        Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.

        Source https://core.telegram.org/bots/api#sendanimation

        :param chat_id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param animation: Animation to send. Pass a file_id as String to send an animation that exists
            on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation
            from the Internet, or upload a new animation using multipart/form-data
        :type animation: :obj:`typing.Union[base.InputFile, base.String]`
        :param duration: Duration of sent animation in seconds
        :type duration: :obj:`typing.Union[base.Integer, None]`
        :param width: Animation width
        :type width: :obj:`typing.Union[base.Integer, None]`
        :param height: Animation height
        :type height: :obj:`typing.Union[base.Integer, None]`
        :param thumb: Thumbnail of the file sent. The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail‘s width and height should not exceed 320.
        :type thumb: :obj:`typing.Union[typing.Union[base.InputFile, base.String], None]`
        :param caption: Animation caption (may also be used when resending animation by file_id), 0-1024 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in the media caption
        :type parse_mode: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[typing.Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup,
            types.ReplyKeyboardRemove, types.ForceReply], None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=["animation", "thumb"])
        if self.parse_mode:
            payload.setdefault('parse_mode', self.parse_mode)

        files = {}
        prepare_file(payload, files, 'animation', animation)
        prepare_attachment(payload, files, 'thumb', thumb)

        result = await self.request(api.Methods.SEND_ANIMATION, payload, files)
        return types.Message(**result)

    async def send_voice(self, chat_id: typing.Union[base.Integer, base.String],
                         voice: typing.Union[base.InputFile, base.String],
                         caption: typing.Union[base.String, None] = None,
                         parse_mode: typing.Union[base.String, None] = None,
                         duration: typing.Union[base.Integer, None] = None,
                         disable_notification: typing.Union[base.Boolean, None] = None,
                         reply_to_message_id: typing.Union[base.Integer, None] = None,
                         reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                    types.ReplyKeyboardMarkup,
                                                    types.ReplyKeyboardRemove,
                                                    types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file
        as a playable voice message.

        For this to work, your audio must be in an .ogg file encoded with OPUS
        (other formats may be sent as Audio or Document).

        Source: https://core.telegram.org/bots/api#sendvoice

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param voice: Audio file to send
        :type voice: :obj:`typing.Union[base.InputFile, base.String]`
        :param caption: Voice message caption, 0-1024 characters
        :type caption: :obj:`typing.Union[base.String, None]`
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Union[base.String, None]`
        :param duration: Duration of the voice message in seconds
        :type duration: :obj:`typing.Union[base.Integer, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['voice'])
        if self.parse_mode:
            payload.setdefault('parse_mode', self.parse_mode)

        files = {}
        prepare_file(payload, files, 'voice', voice)

        result = await self.request(api.Methods.SEND_VOICE, payload, files)
        return types.Message(**result)

    async def send_video_note(self, chat_id: typing.Union[base.Integer, base.String],
                              video_note: typing.Union[base.InputFile, base.String],
                              duration: typing.Union[base.Integer, None] = None,
                              length: typing.Union[base.Integer, None] = None,
                              thumb: typing.Union[base.InputFile, base.String, None] = None,
                              disable_notification: typing.Union[base.Boolean, None] = None,
                              reply_to_message_id: typing.Union[base.Integer, None] = None,
                              reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                         types.ReplyKeyboardMarkup,
                                                         types.ReplyKeyboardRemove,
                                                         types.ForceReply, None] = None) -> types.Message:
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long.
        Use this method to send video messages.

        Source: https://core.telegram.org/bots/api#sendvideonote

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param video_note: Video note to send
        :type video_note: :obj:`typing.Union[base.InputFile, base.String]`
        :param duration: Duration of sent video in seconds
        :type duration: :obj:`typing.Union[base.Integer, None]`
        :param length: Video width and height
        :type length: :obj:`typing.Union[base.Integer, None]`
        :param thumb: Thumbnail of the file sent
        :type thumb: :obj:`typing.Union[base.InputFile, base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup,
            types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['video_note'])

        files = {}
        prepare_file(payload, files, 'video_note', video_note)

        result = await self.request(api.Methods.SEND_VIDEO_NOTE, payload, files)
        return types.Message(**result)

    async def send_media_group(self, chat_id: typing.Union[base.Integer, base.String],
                               media: typing.Union[types.MediaGroup, typing.List],
                               disable_notification: typing.Union[base.Boolean, None] = None,
                               reply_to_message_id: typing.Union[base.Integer,
                                                                 None] = None) -> typing.List[types.Message]:
        """
        Use this method to send a group of photos or videos as an album.

        Source: https://core.telegram.org/bots/api#sendmediagroup

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param media: A JSON-serialized array describing photos and videos to be sent
        :type media: :obj:`typing.Union[types.MediaGroup, typing.List]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :return: On success, an array of the sent Messages is returned
        :rtype: typing.List[types.Message]
        """
        # Convert list to MediaGroup
        if isinstance(media, list):
            media = types.MediaGroup(media)

        files = dict(media.get_files())

        media = prepare_arg(media)
        payload = generate_payload(**locals(), exclude=['files'])

        result = await self.request(api.Methods.SEND_MEDIA_GROUP, payload, files)
        return [types.Message(**message) for message in result]

    async def send_location(self, chat_id: typing.Union[base.Integer, base.String],
                            latitude: base.Float, longitude: base.Float,
                            live_period: typing.Union[base.Integer, None] = None,
                            disable_notification: typing.Union[base.Boolean, None] = None,
                            reply_to_message_id: typing.Union[base.Integer, None] = None,
                            reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                       types.ReplyKeyboardMarkup,
                                                       types.ReplyKeyboardRemove,
                                                       types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send point on the map.

        Source: https://core.telegram.org/bots/api#sendlocation

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param latitude: Latitude of the location
        :type latitude: :obj:`base.Float`
        :param longitude: Longitude of the location
        :type longitude: :obj:`base.Float`
        :param live_period: Period in seconds for which the location will be updated
        :type live_period: :obj:`typing.Union[base.Integer, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SEND_LOCATION, payload)
        return types.Message(**result)

    async def edit_message_live_location(self, latitude: base.Float, longitude: base.Float,
                                         chat_id: typing.Union[base.Integer, base.String, None] = None,
                                         message_id: typing.Union[base.Integer, None] = None,
                                         inline_message_id: typing.Union[base.String, None] = None,
                                         reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                                    None] = None) -> types.Message or base.Boolean:
        """
        Use this method to edit live location messages sent by the bot or via the bot (for inline bots).
        A location can be edited until its live_period expires or editing is explicitly disabled by a call
        to stopMessageLiveLocation.

        Source: https://core.telegram.org/bots/api#editmessagelivelocation

        :param chat_id: Required if inline_message_id is not specified
        :type chat_id: :obj:`typing.Union[base.Integer, base.String, None]`
        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`typing.Union[base.Integer, None]`
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`typing.Union[base.String, None]`
        :param latitude: Latitude of new location
        :type latitude: :obj:`base.Float`
        :param longitude: Longitude of new location
        :type longitude: :obj:`base.Float`
        :param reply_markup: A JSON-serialized object for a new inline keyboard
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, if the edited message was sent by the bot, the edited Message is returned,
            otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.EDIT_MESSAGE_LIVE_LOCATION, payload)
        if isinstance(result, bool):
            return result
        return types.Message(**result)

    async def stop_message_live_location(self,
                                         chat_id: typing.Union[base.Integer, base.String, None] = None,
                                         message_id: typing.Union[base.Integer, None] = None,
                                         inline_message_id: typing.Union[base.String, None] = None,
                                         reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                                    None] = None) -> types.Message or base.Boolean:
        """
        Use this method to stop updating a live location message sent by the bot or via the bot
        (for inline bots) before live_period expires.

        Source: https://core.telegram.org/bots/api#stopmessagelivelocation

        :param chat_id: Required if inline_message_id is not specified
        :type chat_id: :obj:`typing.Union[base.Integer, base.String, None]`
        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`typing.Union[base.Integer, None]`
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`typing.Union[base.String, None]`
        :param reply_markup: A JSON-serialized object for a new inline keyboard
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, if the message was sent by the bot, the sent Message is returned,
            otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.STOP_MESSAGE_LIVE_LOCATION, payload)
        if isinstance(result, bool):
            return result
        return types.Message(**result)

    async def send_venue(self, chat_id: typing.Union[base.Integer, base.String],
                         latitude: base.Float, longitude: base.Float,
                         title: base.String, address: base.String,
                         foursquare_id: typing.Union[base.String, None] = None,
                         foursquare_type: typing.Union[base.String, None] = None,
                         disable_notification: typing.Union[base.Boolean, None] = None,
                         reply_to_message_id: typing.Union[base.Integer, None] = None,
                         reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                    types.ReplyKeyboardMarkup,
                                                    types.ReplyKeyboardRemove,
                                                    types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send information about a venue.

        Source: https://core.telegram.org/bots/api#sendvenue

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
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
        :param foursquare_type: Foursquare type of the venue, if known
        :type foursquare_type: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SEND_VENUE, payload)
        return types.Message(**result)

    async def send_contact(self, chat_id: typing.Union[base.Integer, base.String],
                           phone_number: base.String, first_name: base.String,
                           last_name: typing.Union[base.String, None] = None,
                           vcard: typing.Union[base.String, None] = None,
                           disable_notification: typing.Union[base.Boolean, None] = None,
                           reply_to_message_id: typing.Union[base.Integer, None] = None,
                           reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                      types.ReplyKeyboardMarkup,
                                                      types.ReplyKeyboardRemove,
                                                      types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send phone contacts.

        Source: https://core.telegram.org/bots/api#sendcontact

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param phone_number: Contact's phone number
        :type phone_number: :obj:`base.String`
        :param first_name: Contact's first name
        :type first_name: :obj:`base.String`
        :param last_name: Contact's last name
        :type last_name: :obj:`typing.Union[base.String, None]`
        :param vcard: vcard
        :type vcard: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SEND_CONTACT, payload)
        return types.Message(**result)

    async def send_poll(self, chat_id: typing.Union[base.Integer, base.String],
                        question: base.String,
                        options: typing.List[base.String],
                        is_anonymous: typing.Optional[base.Boolean] = None,
                        type: typing.Optional[base.String] = None,
                        allows_multiple_answers: typing.Optional[base.Boolean] = None,
                        correct_option_id: typing.Optional[base.Integer] = None,
                        explanation: typing.Optional[base.String] = None,
                        explanation_parse_mode: typing.Optional[base.String] = None,
                        open_period: typing.Union[base.Integer, None] = None,
                        close_date: typing.Union[
                            base.Integer, datetime.datetime, datetime.timedelta, None] = None,
                        is_closed: typing.Optional[base.Boolean] = None,
                        disable_notification: typing.Optional[base.Boolean] = None,
                        reply_to_message_id: typing.Optional[base.Integer] = None,
                        reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                   types.ReplyKeyboardMarkup,
                                                   types.ReplyKeyboardRemove,
                                                   types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send a native poll. A native poll can't be sent to a private chat.
        On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendpoll

        :param chat_id: Unique identifier for the target chat
            or username of the target channel (in the format @channelusername).
            A native poll can't be sent to a private chat.
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param question: Poll question, 1-255 characters
        :type question: :obj:`base.String`
        :param options: List of answer options, 2-10 strings 1-100 characters each
        :type options: :obj:`typing.List[base.String]`
        :param is_anonymous: True, if the poll needs to be anonymous, defaults to True
        :type is_anonymous: :obj:`typing.Optional[base.Boolean]`
        :param type: Poll type, “quiz” or “regular”, defaults to “regular”
        :type type: :obj:`typing.Optional[base.String]`
        :param allows_multiple_answers: True, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to False
        :type allows_multiple_answers: :obj:`typing.Optional[base.Boolean]`
        :param correct_option_id: 0-based identifier of the correct answer option, required for polls in quiz mode
        :type correct_option_id: :obj:`typing.Optional[base.Integer]`
        :param explanation: Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing
        :type explanation: :obj:`typing.Optional[base.String]`
        :param explanation_parse_mode: Mode for parsing entities in the explanation. See formatting options for more details.
        :type explanation_parse_mode: :obj:`typing.Optional[base.String]`
        :param open_period: Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with close_date.
        :type open_period: :obj:`typing.Union[base.Integer, None]`
        :param close_date: Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with open_period.
        :type close_date: :obj:`typing.Union[base.Integer, datetime.datetime, datetime.timedelta, None]`
        :param is_closed: Pass True, if the poll needs to be immediately closed
        :type is_closed: :obj:`typing.Optional[base.Boolean]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[Boolean]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Optional[Integer]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        options = prepare_arg(options)
        open_period = prepare_arg(open_period)
        close_date = prepare_arg(close_date)
        payload = generate_payload(**locals())
        if self.parse_mode:
            payload.setdefault('explanation_parse_mode', self.parse_mode)

        result = await self.request(api.Methods.SEND_POLL, payload)
        return types.Message(**result)

    async def send_dice(self, chat_id: typing.Union[base.Integer, base.String],
                        disable_notification: typing.Union[base.Boolean, None] = None,
                        emoji: typing.Union[base.String, None] = None,
                        reply_to_message_id: typing.Union[base.Integer, None] = None,
                        reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                   types.ReplyKeyboardMarkup,
                                                   types.ReplyKeyboardRemove,
                                                   types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send a dice, which will have a random value from 1 to 6.
        On success, the sent Message is returned.
        (Yes, we're aware of the “proper” singular of die.
        But it's awkward, and we decided to help it change. One dice at a time!)

        Source: https://core.telegram.org/bots/api#senddice

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param emoji: Emoji on which the dice throw animation is based. Currently, must be one of “🎲” or “🎯”. Defauts to “🎲”
        :type emoji: :obj:`typing.Union[base.String, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """

        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SEND_DICE, payload)
        return types.Message(**result)

    async def send_chat_action(self, chat_id: typing.Union[base.Integer, base.String],
                               action: base.String) -> base.Boolean:
        """
        Use this method when you need to tell the user that something is happening on the bot's side.
        The status is set for 5 seconds or less
        (when a message arrives from your bot, Telegram clients clear its typing status).

        We only recommend using this method when a response from the bot will take
        a noticeable amount of time to arrive.

        Source: https://core.telegram.org/bots/api#sendchataction

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param action: Type of action to broadcast
        :type action: :obj:`base.String`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SEND_CHAT_ACTION, payload)
        return result

    async def get_user_profile_photos(self, user_id: base.Integer, offset: typing.Union[base.Integer, None] = None,
                                      limit: typing.Union[base.Integer, None] = None) -> types.UserProfilePhotos:
        """
        Use this method to get a list of profile pictures for a user. Returns a UserProfilePhotos object.

        Source: https://core.telegram.org/bots/api#getuserprofilephotos

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`base.Integer`
        :param offset: Sequential number of the first photo to be returned. By default, all photos are returned
        :type offset: :obj:`typing.Union[base.Integer, None]`
        :param limit: Limits the number of photos to be retrieved. Values between 1—100 are accepted. Defaults to 100
        :type limit: :obj:`typing.Union[base.Integer, None]`
        :return: Returns a UserProfilePhotos object
        :rtype: :obj:`types.UserProfilePhotos`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_USER_PROFILE_PHOTOS, payload)
        return types.UserProfilePhotos(**result)

    async def get_file(self, file_id: base.String) -> types.File:
        """
        Use this method to get basic info about a file and prepare it for downloading.
        For the moment, bots can download files of up to 20MB in size.

        Note: This function may not preserve the original file name and MIME type.
        You should save the file's MIME type and name (if available) when the File object is received.

        Source: https://core.telegram.org/bots/api#getfile

        :param file_id: File identifier to get info about
        :type file_id: :obj:`base.String`
        :return: On success, a File object is returned
        :rtype: :obj:`types.File`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_FILE, payload)
        return types.File(**result)

    async def kick_chat_member(self, chat_id: typing.Union[base.Integer, base.String], user_id: base.Integer,
                               until_date: typing.Union[
                                   base.Integer, datetime.datetime, datetime.timedelta, None] = None) -> base.Boolean:
        """
        Use this method to kick a user from a group, a supergroup or a channel.
        In the case of supergroups and channels, the user will not be able to return to the group
        on their own using invite links, etc., unless unbanned first.

        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’ setting
        is off in the target group.
        Otherwise members may only be removed by the group's creator or by the member that added them.

        Source: https://core.telegram.org/bots/api#kickchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`base.Integer`
        :param until_date: Date when the user will be unbanned, unix time
        :type until_date: :obj:`typing.Union[base.Integer, None]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        until_date = prepare_arg(until_date)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.KICK_CHAT_MEMBER, payload)
        return result

    async def unban_chat_member(self, chat_id: typing.Union[base.Integer, base.String],
                                user_id: base.Integer) -> base.Boolean:
        """
        Use this method to unban a previously kicked user in a supergroup or channel. `
        The user will not return to the group or channel automatically, but will be able to join via link, etc.

        The bot must be an administrator for this to work.

        Source: https://core.telegram.org/bots/api#unbanchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`base.Integer`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.UNBAN_CHAT_MEMBER, payload)
        return result

    async def restrict_chat_member(self, chat_id: typing.Union[base.Integer, base.String],
                                   user_id: base.Integer,
                                   permissions: typing.Optional[types.ChatPermissions] = None,
                                   # permissions argument need to be required after removing other `can_*` arguments
                                   until_date: typing.Union[
                                       base.Integer, datetime.datetime, datetime.timedelta, None] = None,
                                   can_send_messages: typing.Union[base.Boolean, None] = None,
                                   can_send_media_messages: typing.Union[base.Boolean, None] = None,
                                   can_send_other_messages: typing.Union[base.Boolean, None] = None,
                                   can_add_web_page_previews: typing.Union[base.Boolean, None] = None) -> base.Boolean:
        """
        Use this method to restrict a user in a supergroup.
        The bot must be an administrator in the supergroup for this to work and must have the appropriate admin rights.
        Pass True for all boolean parameters to lift restrictions from a user.

        Source: https://core.telegram.org/bots/api#restrictchatmember

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`base.Integer`
        :param permissions: New user permissions
        :type permissions: :obj:`ChatPermissions`
        :param until_date: Date when restrictions will be lifted for the user, unix time
        :type until_date: :obj:`typing.Union[base.Integer, None]`
        :param can_send_messages: Pass True, if the user can send text messages, contacts, locations and venues
        :type can_send_messages: :obj:`typing.Union[base.Boolean, None]`
        :param can_send_media_messages: Pass True, if the user can send audios, documents, photos, videos,
            video notes and voice notes, implies can_send_messages
        :type can_send_media_messages: :obj:`typing.Union[base.Boolean, None]`
        :param can_send_other_messages: Pass True, if the user can send animations, games, stickers and
            use inline bots, implies can_send_media_messages
        :type can_send_other_messages: :obj:`typing.Union[base.Boolean, None]`
        :param can_add_web_page_previews: Pass True, if the user may add web page previews to their messages,
            implies can_send_media_messages
        :type can_add_web_page_previews: :obj:`typing.Union[base.Boolean, None]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        until_date = prepare_arg(until_date)
        permissions = prepare_arg(permissions)
        payload = generate_payload(**locals())

        for permission in ('can_send_messages',
                           'can_send_media_messages',
                           'can_send_other_messages',
                           'can_add_web_page_previews'):
            if permission in payload:
                warnings.warn(f"The method `restrict_chat_member` now takes the new user permissions "
                              f"in a single argument of the type ChatPermissions instead of "
                              f"passing regular argument {payload[permission]}",
                              DeprecationWarning, stacklevel=2)

        result = await self.request(api.Methods.RESTRICT_CHAT_MEMBER, payload)
        return result

    async def promote_chat_member(self, chat_id: typing.Union[base.Integer, base.String],
                                  user_id: base.Integer,
                                  can_change_info: typing.Union[base.Boolean, None] = None,
                                  can_post_messages: typing.Union[base.Boolean, None] = None,
                                  can_edit_messages: typing.Union[base.Boolean, None] = None,
                                  can_delete_messages: typing.Union[base.Boolean, None] = None,
                                  can_invite_users: typing.Union[base.Boolean, None] = None,
                                  can_restrict_members: typing.Union[base.Boolean, None] = None,
                                  can_pin_messages: typing.Union[base.Boolean, None] = None,
                                  can_promote_members: typing.Union[base.Boolean, None] = None) -> base.Boolean:
        """
        Use this method to promote or demote a user in a supergroup or a channel.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Pass False for all boolean parameters to demote a user.

        Source: https://core.telegram.org/bots/api#promotechatmember

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`base.Integer`
        :param can_change_info: Pass True, if the administrator can change chat title, photo and other settings
        :type can_change_info: :obj:`typing.Union[base.Boolean, None]`
        :param can_post_messages: Pass True, if the administrator can create channel posts, channels only
        :type can_post_messages: :obj:`typing.Union[base.Boolean, None]`
        :param can_edit_messages: Pass True, if the administrator can edit messages of other users, channels only
        :type can_edit_messages: :obj:`typing.Union[base.Boolean, None]`
        :param can_delete_messages: Pass True, if the administrator can delete messages of other users
        :type can_delete_messages: :obj:`typing.Union[base.Boolean, None]`
        :param can_invite_users: Pass True, if the administrator can invite new users to the chat
        :type can_invite_users: :obj:`typing.Union[base.Boolean, None]`
        :param can_restrict_members: Pass True, if the administrator can restrict, ban or unban chat members
        :type can_restrict_members: :obj:`typing.Union[base.Boolean, None]`
        :param can_pin_messages: Pass True, if the administrator can pin messages, supergroups only
        :type can_pin_messages: :obj:`typing.Union[base.Boolean, None]`
        :param can_promote_members: Pass True, if the administrator can add new administrators
            with a subset of his own privileges or demote administrators that he has promoted,
            directly or indirectly (promoted by administrators that were appointed by him)
        :type can_promote_members: :obj:`typing.Union[base.Boolean, None]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.PROMOTE_CHAT_MEMBER, payload)
        return result

    async def set_chat_administrator_custom_title(self, chat_id: typing.Union[base.Integer, base.String],
                                                  user_id: base.Integer, custom_title: base.String) -> base.Boolean:
        """
        Use this method to set a custom title for an administrator in a supergroup promoted by the bot.

        Returns True on success.

        Source: https://core.telegram.org/bots/api#setchatadministratorcustomtitle

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        :param user_id: Unique identifier of the target user
        :param custom_title: New custom title for the administrator; 0-16 characters, emoji are not allowed
        :return: True on success.
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SET_CHAT_ADMINISTRATOR_CUSTOM_TITLE, payload)
        return result

    async def set_chat_permissions(self, chat_id: typing.Union[base.Integer, base.String],
                                   permissions: types.ChatPermissions) -> base.Boolean:
        """
        Use this method to set default chat permissions for all members.
        The bot must be an administrator in the group or a supergroup for this to work and must have the
        can_restrict_members admin rights.

        Returns True on success.

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        :param permissions: New default chat permissions
        :return: True on success.
        """
        permissions = prepare_arg(permissions)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SET_CHAT_PERMISSIONS, payload)
        return result

    async def export_chat_invite_link(self, chat_id: typing.Union[base.Integer, base.String]) -> base.String:
        """
        Use this method to generate a new invite link for a chat; any previously generated link is revoked.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Source: https://core.telegram.org/bots/api#exportchatinvitelink

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :return: Returns exported invite link as String on success
        :rtype: :obj:`base.String`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.EXPORT_CHAT_INVITE_LINK, payload)
        return result

    async def set_chat_photo(self, chat_id: typing.Union[base.Integer, base.String],
                             photo: base.InputFile) -> base.Boolean:
        """
        Use this method to set a new profile photo for the chat. Photos can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
        setting is off in the target group.

        Source: https://core.telegram.org/bots/api#setchatphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param photo: New chat photo, uploaded using multipart/form-data
        :type photo: :obj:`base.InputFile`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals(), exclude=['photo'])

        files = {}
        prepare_file(payload, files, 'photo', photo)

        result = await self.request(api.Methods.SET_CHAT_PHOTO, payload, files)
        return result

    async def delete_chat_photo(self, chat_id: typing.Union[base.Integer, base.String]) -> base.Boolean:
        """
        Use this method to delete a chat photo. Photos can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
        setting is off in the target group.

        Source: https://core.telegram.org/bots/api#deletechatphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.DELETE_CHAT_PHOTO, payload)
        return result

    async def set_chat_title(self, chat_id: typing.Union[base.Integer, base.String],
                             title: base.String) -> base.Boolean:
        """
        Use this method to change the title of a chat. Titles can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
        setting is off in the target group.

        Source: https://core.telegram.org/bots/api#setchattitle

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param title: New chat title, 1-255 characters
        :type title: :obj:`base.String`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SET_CHAT_TITLE, payload)
        return result

    async def set_chat_description(self, chat_id: typing.Union[base.Integer, base.String],
                                   description: typing.Union[base.String, None] = None) -> base.Boolean:
        """
        Use this method to change the description of a supergroup or a channel.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Source: https://core.telegram.org/bots/api#setchatdescription

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param description: New chat description, 0-255 characters
        :type description: :obj:`typing.Union[base.String, None]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SET_CHAT_DESCRIPTION, payload)
        return result

    async def pin_chat_message(self, chat_id: typing.Union[base.Integer, base.String], message_id: base.Integer,
                               disable_notification: typing.Union[base.Boolean, None] = None) -> base.Boolean:
        """
        Use this method to pin a message in a supergroup.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Source: https://core.telegram.org/bots/api#pinchatmessage

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param message_id: Identifier of a message to pin
        :type message_id: :obj:`base.Integer`
        :param disable_notification: Pass True, if it is not necessary to send a notification to
            all group members about the new pinned message
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.PIN_CHAT_MESSAGE, payload)
        return result

    async def unpin_chat_message(self, chat_id: typing.Union[base.Integer, base.String]) -> base.Boolean:
        """
        Use this method to unpin a message in a supergroup chat.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Source: https://core.telegram.org/bots/api#unpinchatmessage

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.UNPIN_CHAT_MESSAGE, payload)
        return result

    async def leave_chat(self, chat_id: typing.Union[base.Integer, base.String]) -> base.Boolean:
        """
        Use this method for your bot to leave a group, supergroup or channel.

        Source: https://core.telegram.org/bots/api#leavechat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.LEAVE_CHAT, payload)
        return result

    async def get_chat(self, chat_id: typing.Union[base.Integer, base.String]) -> types.Chat:
        """
        Use this method to get up to date information about the chat
        (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.).

        Source: https://core.telegram.org/bots/api#getchat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :return: Returns a Chat object on success
        :rtype: :obj:`types.Chat`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_CHAT, payload)
        return types.Chat(**result)

    async def get_chat_administrators(self, chat_id: typing.Union[base.Integer, base.String]
                                      ) -> typing.List[types.ChatMember]:
        """
        Use this method to get a list of administrators in a chat.

        Source: https://core.telegram.org/bots/api#getchatadministrators

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :return: On success, returns an Array of ChatMember objects that contains information about all
            chat administrators except other bots.
            If the chat is a group or a supergroup and no administrators were appointed,
            only the creator will be returned.
        :rtype: :obj:`typing.List[types.ChatMember]`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_CHAT_ADMINISTRATORS, payload)
        return [types.ChatMember(**chatmember) for chatmember in result]

    async def get_chat_members_count(self, chat_id: typing.Union[base.Integer, base.String]) -> base.Integer:
        """
        Use this method to get the number of members in a chat.

        Source: https://core.telegram.org/bots/api#getchatmemberscount

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :return: Returns Int on success
        :rtype: :obj:`base.Integer`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_CHAT_MEMBERS_COUNT, payload)
        return result

    async def get_chat_member(self, chat_id: typing.Union[base.Integer, base.String],
                              user_id: base.Integer) -> types.ChatMember:
        """
        Use this method to get information about a member of a chat.

        Source: https://core.telegram.org/bots/api#getchatmember

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`base.Integer`
        :return: Returns a ChatMember object on success
        :rtype: :obj:`types.ChatMember`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_CHAT_MEMBER, payload)
        return types.ChatMember(**result)

    async def set_chat_sticker_set(self, chat_id: typing.Union[base.Integer, base.String],
                                   sticker_set_name: base.String) -> base.Boolean:
        """
        Use this method to set a new group sticker set for a supergroup.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Use the field can_set_sticker_set optionally returned in getChat requests to check
        if the bot can use this method.

        Source: https://core.telegram.org/bots/api#setchatstickerset

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param sticker_set_name: Name of the sticker set to be set as the group sticker set
        :type sticker_set_name: :obj:`base.String`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SET_CHAT_STICKER_SET, payload)
        return result

    async def delete_chat_sticker_set(self, chat_id: typing.Union[base.Integer, base.String]) -> base.Boolean:
        """
        Use this method to delete a group sticker set from a supergroup.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Use the field can_set_sticker_set optionally returned in getChat requests
        to check if the bot can use this method.

        Source: https://core.telegram.org/bots/api#deletechatstickerset

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.DELETE_CHAT_STICKER_SET, payload)
        return result

    async def answer_callback_query(self, callback_query_id: base.String,
                                    text: typing.Union[base.String, None] = None,
                                    show_alert: typing.Union[base.Boolean, None] = None,
                                    url: typing.Union[base.String, None] = None,
                                    cache_time: typing.Union[base.Integer, None] = None) -> base.Boolean:
        """
        Use this method to send answers to callback queries sent from inline keyboards.
        The answer will be displayed to the user as a notification at the top of the chat screen or as an alert.

        Alternatively, the user can be redirected to the specified Game URL.
        For this option to work, you must first create a game for your bot via @Botfather and accept the terms.
        Otherwise, you may use links like t.me/your_bot?start=XXXX that open your bot with a parameter.

        Source: https://core.telegram.org/bots/api#answercallbackquery

        :param callback_query_id: Unique identifier for the query to be answered
        :type callback_query_id: :obj:`base.String`
        :param text: Text of the notification. If not specified, nothing will be shown to the user, 0-1024 characters
        :type text: :obj:`typing.Union[base.String, None]`
        :param show_alert: If true, an alert will be shown by the client instead of a notification
            at the top of the chat screen. Defaults to false.
        :type show_alert: :obj:`typing.Union[base.Boolean, None]`
        :param url: URL that will be opened by the user's client
        :type url: :obj:`typing.Union[base.String, None]`
        :param cache_time: The maximum amount of time in seconds that the
            result of the callback query may be cached client-side.
        :type cache_time: :obj:`typing.Union[base.Integer, None]`
        :return: On success, True is returned
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.ANSWER_CALLBACK_QUERY, payload)
        return result

    async def set_my_commands(self, commands: typing.List[types.BotCommand]) -> base.Boolean:
        """
        Use this method to change the list of the bot's commands.

        Source: https://core.telegram.org/bots/api#setmycommands

        :param commands: A JSON-serialized list of bot commands to be set as the list of the bot's commands.
            At most 100 commands can be specified.
        :type commands: :obj: `typing.List[types.BotCommand]`
        :return: Returns True on success.
        :rtype: :obj:`base.Boolean`
        """
        commands = prepare_arg(commands)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SET_MY_COMMANDS, payload)
        return result

    async def get_my_commands(self) -> typing.List[types.BotCommand]:
        """
        Use this method to get the current list of the bot's commands.

        Source: https://core.telegram.org/bots/api#getmycommands
        :return: Returns Array of BotCommand on success.
        :rtype: :obj:`typing.List[types.BotCommand]`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_MY_COMMANDS, payload)
        return [types.BotCommand(**bot_command_data) for bot_command_data in result]

    async def edit_message_text(self, text: base.String,
                                chat_id: typing.Union[base.Integer, base.String, None] = None,
                                message_id: typing.Union[base.Integer, None] = None,
                                inline_message_id: typing.Union[base.String, None] = None,
                                parse_mode: typing.Union[base.String, None] = None,
                                disable_web_page_preview: typing.Union[base.Boolean, None] = None,
                                reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                           None] = None) -> types.Message or base.Boolean:
        """
        Use this method to edit text and game messages sent by the bot or via the bot (for inline bots).

        Source: https://core.telegram.org/bots/api#editmessagetext

        :param chat_id: Required if inline_message_id is not specified
            Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String, None]`
        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`typing.Union[base.Integer, None]`
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`typing.Union[base.String, None]`
        :param text: New text of the message
        :type text: :obj:`base.String`
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Union[base.String, None]`
        :param disable_web_page_preview: Disables link previews for links in this message
        :type disable_web_page_preview: :obj:`typing.Union[base.Boolean, None]`
        :param reply_markup: A JSON-serialized object for an inline keyboard
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, if edited message is sent by the bot,
            the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())
        if self.parse_mode:
            payload.setdefault('parse_mode', self.parse_mode)

        result = await self.request(api.Methods.EDIT_MESSAGE_TEXT, payload)
        if isinstance(result, bool):
            return result
        return types.Message(**result)

    async def edit_message_caption(self, chat_id: typing.Union[base.Integer, base.String, None] = None,
                                   message_id: typing.Union[base.Integer, None] = None,
                                   inline_message_id: typing.Union[base.String, None] = None,
                                   caption: typing.Union[base.String, None] = None,
                                   parse_mode: typing.Union[base.String, None] = None,
                                   reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                              None] = None) -> types.Message or base.Boolean:
        """
        Use this method to edit captions of messages sent by the bot or via the bot (for inline bots).

        Source: https://core.telegram.org/bots/api#editmessagecaption

        :param chat_id: Required if inline_message_id is not specified
            Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String, None]`
        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`typing.Union[base.Integer, None]`
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`typing.Union[base.String, None]`
        :param caption: New caption of the message
        :type caption: :obj:`typing.Union[base.String, None]`
        :param parse_mode: Send Markdown or HTML, if you want Telegram apps to show bold, italic,
            fixed-width text or inline URLs in your bot's message.
        :type parse_mode: :obj:`typing.Union[base.String, None]`
        :param reply_markup: A JSON-serialized object for an inline keyboard
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, if edited message is sent by the bot, the edited Message is returned,
            otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())
        if self.parse_mode:
            payload.setdefault('parse_mode', self.parse_mode)

        result = await self.request(api.Methods.EDIT_MESSAGE_CAPTION, payload)
        if isinstance(result, bool):
            return result
        return types.Message(**result)

    async def edit_message_media(self,
                                 media: types.InputMedia,
                                 chat_id: typing.Union[typing.Union[base.Integer, base.String], None] = None,
                                 message_id: typing.Union[base.Integer, None] = None,
                                 inline_message_id: typing.Union[base.String, None] = None,
                                 reply_markup: typing.Union[types.InlineKeyboardMarkup, None] = None,
                                 ) -> typing.Union[types.Message, base.Boolean]:
        """
        Use this method to edit audio, document, photo, or video messages.
        If a message is a part of a message album, then it can be edited only to a photo or a video.
        Otherwise, message type can be changed arbitrarily.
        When inline message is edited, new file can't be uploaded.
        Use previously uploaded file via its file_id or specify a URL.

        On success, if the edited message was sent by the bot,
        the edited Message is returned, otherwise True is returned.

        Source https://core.telegram.org/bots/api#editmessagemedia

        :param chat_id: Required if inline_message_id is not specified
        :type chat_id: :obj:`typing.Union[typing.Union[base.Integer, base.String], None]`
        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`typing.Union[base.Integer, None]`
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`typing.Union[base.String, None]`
        :param media: A JSON-serialized object for a new media content of the message
        :type media: :obj:`types.InputMedia`
        :param reply_markup: A JSON-serialized object for a new inline keyboard
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, if the edited message was sent by the bot, the edited Message is returned,
            otherwise True is returned
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        if isinstance(media, types.InputMedia):
            files = dict(media.get_files())
        else:
            files = None

        result = await self.request(api.Methods.EDIT_MESSAGE_MEDIA, payload, files)
        if isinstance(result, bool):
            return result
        return types.Message(**result)

    async def edit_message_reply_markup(self,
                                        chat_id: typing.Union[base.Integer, base.String, None] = None,
                                        message_id: typing.Union[base.Integer, None] = None,
                                        inline_message_id: typing.Union[base.String, None] = None,
                                        reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                                   None] = None) -> types.Message or base.Boolean:
        """
        Use this method to edit only the reply markup of messages sent by the bot or via the bot (for inline bots).

        Source: https://core.telegram.org/bots/api#editmessagereplymarkup

        :param chat_id: Required if inline_message_id is not specified
            Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String, None]`
        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`typing.Union[base.Integer, None]`
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`typing.Union[base.String, None]`
        :param reply_markup: A JSON-serialized object for an inline keyboard
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, if edited message is sent by the bot, the edited Message is returned,
            otherwise True is returned.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.EDIT_MESSAGE_REPLY_MARKUP, payload)
        if isinstance(result, bool):
            return result
        return types.Message(**result)

    async def stop_poll(self, chat_id: typing.Union[base.String, base.Integer],
                        message_id: base.Integer,
                        reply_markup: typing.Union[types.InlineKeyboardMarkup, None] = None) -> types.Poll:
        """
        Use this method to stop a poll which was sent by the bot.
        On success, the stopped Poll with the final results is returned.

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.String, base.Integer]`
        :param message_id: Identifier of the original message with the poll
        :type message_id: :obj:`base.Integer`
        :param reply_markup: A JSON-serialized object for a new message inline keyboard.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, the stopped Poll with the final results is returned.
        :rtype: :obj:`types.Poll`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.STOP_POLL, payload)
        return types.Poll(**result)

    async def delete_message(self, chat_id: typing.Union[base.Integer, base.String],
                             message_id: base.Integer) -> base.Boolean:
        """
        Use this method to delete a message, including service messages, with the following limitations:
        - A message can only be deleted if it was sent less than 48 hours ago.
        - Bots can delete outgoing messages in private chats, groups, and supergroups.
        - Bots can delete incoming messages in private chats.
        - Bots granted can_post_messages permissions can delete outgoing messages in channels.
        - If the bot is an administrator of a group, it can delete any message there.
        - If the bot has can_delete_messages permission in a supergroup or a channel, it can delete any message there.

        Source: https://core.telegram.org/bots/api#deletemessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param message_id: Identifier of the message to delete
        :type message_id: :obj:`base.Integer`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.DELETE_MESSAGE, payload)
        return result

    # === Stickers ===
    # https://core.telegram.org/bots/api#stickers

    async def send_sticker(self, chat_id: typing.Union[base.Integer, base.String],
                           sticker: typing.Union[base.InputFile, base.String],
                           disable_notification: typing.Union[base.Boolean, None] = None,
                           reply_to_message_id: typing.Union[base.Integer, None] = None,
                           reply_markup: typing.Union[types.InlineKeyboardMarkup,
                                                      types.ReplyKeyboardMarkup,
                                                      types.ReplyKeyboardRemove,
                                                      types.ForceReply, None] = None) -> types.Message:
        """
        Use this method to send .webp stickers.

        Source: https://core.telegram.org/bots/api#sendsticker

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param sticker: Sticker to send
        :type sticker: :obj:`typing.Union[base.InputFile, base.String]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup,
            types.ReplyKeyboardMarkup, types.ReplyKeyboardRemove, types.ForceReply, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['sticker'])

        files = {}
        prepare_file(payload, files, 'sticker', sticker)

        result = await self.request(api.Methods.SEND_STICKER, payload, files)
        return types.Message(**result)

    async def get_sticker_set(self, name: base.String) -> types.StickerSet:
        """
        Use this method to get a sticker set.

        Source: https://core.telegram.org/bots/api#getstickerset

        :param name: Name of the sticker set
        :type name: :obj:`base.String`
        :return: On success, a StickerSet object is returned
        :rtype: :obj:`types.StickerSet`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.GET_STICKER_SET, payload)
        return types.StickerSet(**result)

    async def upload_sticker_file(self, user_id: base.Integer, png_sticker: base.InputFile) -> types.File:
        """
        Use this method to upload a .png file with a sticker for later use in createNewStickerSet
        and addStickerToSet methods (can be used multiple times).

        Source: https://core.telegram.org/bots/api#uploadstickerfile

        :param user_id: User identifier of sticker file owner
        :type user_id: :obj:`base.Integer`
        :param png_sticker: Png image with the sticker, must be up to 512 kilobytes in size,
            dimensions must not exceed 512px, and either width or height must be exactly 512px.
        :type png_sticker: :obj:`base.InputFile`
        :return: Returns the uploaded File on success
        :rtype: :obj:`types.File`
        """
        payload = generate_payload(**locals(), exclude=['png_sticker'])

        files = {}
        prepare_file(payload, files, 'png_sticker', png_sticker)

        result = await self.request(api.Methods.UPLOAD_STICKER_FILE, payload, files)
        return types.File(**result)

    async def create_new_sticker_set(self,
                                     user_id: base.Integer,
                                     name: base.String,
                                     title: base.String,
                                     emojis: base.String,
                                     png_sticker: typing.Union[base.InputFile, base.String] = None,
                                     tgs_sticker: base.InputFile = None,
                                     contains_masks: typing.Union[base.Boolean, None] = None,
                                     mask_position: typing.Union[types.MaskPosition, None] = None) -> base.Boolean:
        """
        Use this method to create a new sticker set owned by a user.
        The bot will be able to edit the sticker set thus created.
        You must use exactly one of the fields png_sticker or tgs_sticker.

        Source: https://core.telegram.org/bots/api#createnewstickerset

        :param user_id: User identifier of created sticker set owner
        :type user_id: :obj:`base.Integer`
        :param name: Short name of sticker set, to be used in t.me/addstickers/ URLs (e.g., animals).
            Can contain only english letters, digits and underscores.
            Must begin with a letter, can't contain consecutive underscores and must end in “_by_<bot username>”.
            <bot_username> is case insensitive. 1-64 characters.
        :type name: :obj:`base.String`
        :param title: Sticker set title, 1-64 characters
        :type title: :obj:`base.String`
        :param png_sticker: PNG image with the sticker, must be up to 512 kilobytes in size,
            dimensions must not exceed 512px, and either width or height must be exactly 512px.
            Pass a file_id as a String to send a file that already exists on the Telegram servers,
            pass an HTTP URL as a String for Telegram to get a file from the Internet, or
            upload a new one using multipart/form-data. More info on https://core.telegram.org/bots/api#sending-files
        :type png_sticker: :obj:`typing.Union[base.InputFile, base.String]`
        :param tgs_sticker: TGS animation with the sticker, uploaded using multipart/form-data.
            See https://core.telegram.org/animated_stickers#technical-requirements for technical requirements
        :type tgs_sticker: :obj:`base.InputFile`
        :param emojis: One or more emoji corresponding to the sticker
        :type emojis: :obj:`base.String`
        :param contains_masks: Pass True, if a set of mask stickers should be created
        :type contains_masks: :obj:`typing.Union[base.Boolean, None]`
        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces
        :type mask_position: :obj:`typing.Union[types.MaskPosition, None]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        mask_position = prepare_arg(mask_position)
        payload = generate_payload(**locals(), exclude=['png_sticker', 'tgs_sticker'])

        files = {}
        prepare_file(payload, files, 'png_sticker', png_sticker)
        prepare_file(payload, files, 'tgs_sticker', tgs_sticker)

        result = await self.request(api.Methods.CREATE_NEW_STICKER_SET, payload, files)
        return result

    async def add_sticker_to_set(self,
                                 user_id: base.Integer,
                                 name: base.String,
                                 emojis: base.String,
                                 png_sticker: typing.Union[base.InputFile, base.String] = None,
                                 tgs_sticker: base.InputFile = None,
                                 mask_position: typing.Union[types.MaskPosition, None] = None) -> base.Boolean:
        """
        Use this method to add a new sticker to a set created by the bot.
        You must use exactly one of the fields png_sticker or tgs_sticker.
        Animated stickers can be added to animated sticker sets and only to them.
        Animated sticker sets can have up to 50 stickers.
        Static sticker sets can have up to 120 stickers.

        Source: https://core.telegram.org/bots/api#addstickertoset

        :param user_id: User identifier of sticker set owner
        :type user_id: :obj:`base.Integer`
        :param name: Sticker set name
        :type name: :obj:`base.String`
        :param png_sticker: PNG image with the sticker, must be up to 512 kilobytes in size,
            dimensions must not exceed 512px, and either width or height must be exactly 512px.
            Pass a file_id as a String to send a file that already exists on the Telegram servers,
            pass an HTTP URL as a String for Telegram to get a file from the Internet, or
            upload a new one using multipart/form-data. More info on https://core.telegram.org/bots/api#sending-files
        :type png_sticker: :obj:`typing.Union[base.InputFile, base.String]`
        :param tgs_sticker: TGS animation with the sticker, uploaded using multipart/form-data.
            See https://core.telegram.org/animated_stickers#technical-requirements for technical requirements
        :type tgs_sticker: :obj:`base.InputFile`
        :param emojis: One or more emoji corresponding to the sticker
        :type emojis: :obj:`base.String`
        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces
        :type mask_position: :obj:`typing.Union[types.MaskPosition, None]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        mask_position = prepare_arg(mask_position)
        payload = generate_payload(**locals(), exclude=['png_sticker', 'tgs_sticker'])

        files = {}
        prepare_file(payload, files, 'png_sticker', png_sticker)
        prepare_file(payload, files, 'tgs_sticker', tgs_sticker)

        result = await self.request(api.Methods.ADD_STICKER_TO_SET, payload, files)
        return result

    async def set_sticker_position_in_set(self, sticker: base.String, position: base.Integer) -> base.Boolean:
        """
        Use this method to move a sticker in a set created by the bot to a specific position.

        Source: https://core.telegram.org/bots/api#setstickerpositioninset

        :param sticker: File identifier of the sticker
        :type sticker: :obj:`base.String`
        :param position: New sticker position in the set, zero-based
        :type position: :obj:`base.Integer`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())
        result = await self.request(api.Methods.SET_STICKER_POSITION_IN_SET, payload)

        return result

    async def delete_sticker_from_set(self, sticker: base.String) -> base.Boolean:
        """
        Use this method to delete a sticker from a set created by the bot.

        Source: https://core.telegram.org/bots/api#deletestickerfromset

        :param sticker: File identifier of the sticker
        :type sticker: :obj:`base.String`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.DELETE_STICKER_FROM_SET, payload)
        return result

    async def set_sticker_set_thumb(self,
                                    name: base.String,
                                    user_id: base.Integer,
                                    thumb: typing.Union[base.InputFile, base.String] = None) -> base.Boolean:
        """
        Use this method to set the thumbnail of a sticker set.
        Animated thumbnails can be set for animated sticker sets only.

        Source: https://core.telegram.org/bots/api#setstickersetthumb

        :param name: Sticker set name
        :type name: :obj:`base.String`
        :param user_id: User identifier of the sticker set owner
        :type user_id: :obj:`base.Integer`
        :param thumb: A PNG image with the thumbnail, must be up to 128 kilobytes in size and have width and height
            exactly 100px, or a TGS animation with the thumbnail up to 32 kilobytes in size;
            see https://core.telegram.org/animated_stickers#technical-requirements for animated sticker technical
            requirements. Pass a file_id as a String to send a file that already exists on the Telegram servers,
            pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using
            multipart/form-data. More info on https://core.telegram.org/bots/api#sending-files.
            Animated sticker set thumbnail can't be uploaded via HTTP URL.
        :type thumb: :obj:`typing.Union[base.InputFile, base.String]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals(), exclude=['thumb'])

        files = {}
        prepare_file(payload, files, 'thumb', thumb)

        result = await self.request(api.Methods.SET_STICKER_SET_THUMB, payload, files)
        return result

    async def answer_inline_query(self, inline_query_id: base.String,
                                  results: typing.List[types.InlineQueryResult],
                                  cache_time: typing.Union[base.Integer, None] = None,
                                  is_personal: typing.Union[base.Boolean, None] = None,
                                  next_offset: typing.Union[base.String, None] = None,
                                  switch_pm_text: typing.Union[base.String, None] = None,
                                  switch_pm_parameter: typing.Union[base.String, None] = None) -> base.Boolean:
        """
        Use this method to send answers to an inline query.
        No more than 50 results per query are allowed.

        Source: https://core.telegram.org/bots/api#answerinlinequery

        :param inline_query_id: Unique identifier for the answered query
        :type inline_query_id: :obj:`base.String`
        :param results: A JSON-serialized array of results for the inline query
        :type results: :obj:`typing.List[types.InlineQueryResult]`
        :param cache_time: The maximum amount of time in seconds that the result of the
            inline query may be cached on the server. Defaults to 300.
        :type cache_time: :obj:`typing.Union[base.Integer, None]`
        :param is_personal: Pass True, if results may be cached on the server side only
            for the user that sent the query. By default, results may be returned to any user who sends the same query
        :type is_personal: :obj:`typing.Union[base.Boolean, None]`
        :param next_offset: Pass the offset that a client should send in the
            next query with the same text to receive more results.
            Pass an empty string if there are no more results or if you don‘t support pagination.
            Offset length can’t exceed 64 bytes.
        :type next_offset: :obj:`typing.Union[base.String, None]`
        :param switch_pm_text: If passed, clients will display a button with specified text that
            switches the user to a private chat with the bot and sends the bot a start message
            with the parameter switch_pm_parameter
        :type switch_pm_text: :obj:`typing.Union[base.String, None]`
        :param switch_pm_parameter: Deep-linking parameter for the /start message sent to the bot when
            user presses the switch button. 1-64 characters, only A-Z, a-z, 0-9, _ and - are allowed.
        :type switch_pm_parameter: :obj:`typing.Union[base.String, None]`
        :return: On success, True is returned
        :rtype: :obj:`base.Boolean`
        """
        results = prepare_arg(results)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.ANSWER_INLINE_QUERY, payload)
        return result

    # === Payments ===
    # https://core.telegram.org/bots/api#payments

    async def send_invoice(self, chat_id: base.Integer, title: base.String,
                           description: base.String, payload: base.String,
                           provider_token: base.String, start_parameter: base.String,
                           currency: base.String, prices: typing.List[types.LabeledPrice],
                           provider_data: typing.Union[typing.Dict, None] = None,
                           photo_url: typing.Union[base.String, None] = None,
                           photo_size: typing.Union[base.Integer, None] = None,
                           photo_width: typing.Union[base.Integer, None] = None,
                           photo_height: typing.Union[base.Integer, None] = None,
                           need_name: typing.Union[base.Boolean, None] = None,
                           need_phone_number: typing.Union[base.Boolean, None] = None,
                           need_email: typing.Union[base.Boolean, None] = None,
                           need_shipping_address: typing.Union[base.Boolean, None] = None,
                           send_phone_number_to_provider: typing.Union[base.Boolean, None] = None,
                           send_email_to_provider: typing.Union[base.Boolean, None] = None,
                           is_flexible: typing.Union[base.Boolean, None] = None,
                           disable_notification: typing.Union[base.Boolean, None] = None,
                           reply_to_message_id: typing.Union[base.Integer, None] = None,
                           reply_markup: typing.Union[types.InlineKeyboardMarkup, None] = None) -> types.Message:
        """
        Use this method to send invoices.

        Source: https://core.telegram.org/bots/api#sendinvoice

        :param chat_id: Unique identifier for the target private chat
        :type chat_id: :obj:`base.Integer`
        :param title: Product name, 1-32 characters
        :type title: :obj:`base.String`
        :param description: Product description, 1-255 characters
        :type description: :obj:`base.String`
        :param payload: Bot-defined invoice payload, 1-128 bytes
            This will not be displayed to the user, use for your internal processes.
        :type payload: :obj:`base.String`
        :param provider_token: Payments provider token, obtained via Botfather
        :type provider_token: :obj:`base.String`
        :param start_parameter: Unique deep-linking parameter that can be used to generate this
            invoice when used as a start parameter
        :type start_parameter: :obj:`base.String`
        :param currency: Three-letter ISO 4217 currency code, see more on currencies
        :type currency: :obj:`base.String`
        :param prices: Price breakdown, a list of components
            (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :type prices: :obj:`typing.List[types.LabeledPrice]`
        :param provider_data: JSON-encoded data about the invoice, which will be shared with the payment provider
        :type provider_data: :obj:`typing.Union[typing.Dict, None]`
        :param photo_url: URL of the product photo for the invoice
        :type photo_url: :obj:`typing.Union[base.String, None]`
        :param photo_size: Photo size
        :type photo_size: :obj:`typing.Union[base.Integer, None]`
        :param photo_width: Photo width
        :type photo_width: :obj:`typing.Union[base.Integer, None]`
        :param photo_height: Photo height
        :type photo_height: :obj:`typing.Union[base.Integer, None]`
        :param need_name: Pass True, if you require the user's full name to complete the order
        :type need_name: :obj:`typing.Union[base.Boolean, None]`
        :param need_phone_number: Pass True, if you require the user's phone number to complete the order
        :type need_phone_number: :obj:`typing.Union[base.Boolean, None]`
        :param need_email: Pass True, if you require the user's email to complete the order
        :type need_email: :obj:`typing.Union[base.Boolean, None]`
        :param need_shipping_address: Pass True, if you require the user's shipping address to complete the order
        :type need_shipping_address: :obj:`typing.Union[base.Boolean, None]`
        :param send_phone_number_to_provider: Pass True, if user's phone number should be sent to provider
        :type send_phone_number_to_provider: :obj:`typing.Union[base.Boolean, None]`
        :param send_email_to_provider: Pass True, if user's email address should be sent to provider
        :type send_email_to_provider: :obj:`typing.Union[base.Boolean, None]`
        :param is_flexible: Pass True, if the final price depends on the shipping method
        :type is_flexible: :obj:`typing.Union[base.Boolean, None]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: A JSON-serialized object for an inline keyboard
            If empty, one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        prices = prepare_arg([price.to_python() if hasattr(price, 'to_python') else price for price in prices])
        reply_markup = prepare_arg(reply_markup)
        payload_ = generate_payload(**locals())

        result = await self.request(api.Methods.SEND_INVOICE, payload_)
        return types.Message(**result)

    async def answer_shipping_query(self, shipping_query_id: base.String, ok: base.Boolean,
                                    shipping_options: typing.Union[typing.List[types.ShippingOption], None] = None,
                                    error_message: typing.Union[base.String, None] = None) -> base.Boolean:
        """
        If you sent an invoice requesting a shipping address and the parameter is_flexible was specified,
        the Bot API will send an Update with a shipping_query field to the bot.

        Source: https://core.telegram.org/bots/api#answershippingquery

        :param shipping_query_id: Unique identifier for the query to be answered
        :type shipping_query_id: :obj:`base.String`
        :param ok: Specify True if delivery to the specified address is possible and False if there are any problems
            (for example, if delivery to the specified address is not possible)
        :type ok: :obj:`base.Boolean`
        :param shipping_options: Required if ok is True. A JSON-serialized array of available shipping options
        :type shipping_options: :obj:`typing.Union[typing.List[types.ShippingOption], None]`
        :param error_message: Required if ok is False
            Error message in human readable form that explains why it is impossible to complete the order
            (e.g. "Sorry, delivery to your desired address is unavailable').
            Telegram will display this message to the user.
        :type error_message: :obj:`typing.Union[base.String, None]`
        :return: On success, True is returned
        :rtype: :obj:`base.Boolean`
        """
        if shipping_options:
            shipping_options = prepare_arg([shipping_option.to_python()
                                            if hasattr(shipping_option, 'to_python')
                                            else shipping_option
                                            for shipping_option in shipping_options])
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.ANSWER_SHIPPING_QUERY, payload)
        return result

    async def answer_pre_checkout_query(self, pre_checkout_query_id: base.String, ok: base.Boolean,
                                        error_message: typing.Union[base.String, None] = None) -> base.Boolean:
        """
        Once the user has confirmed their payment and shipping details,
        the Bot API sends the final confirmation in the form of an Update with the field pre_checkout_query.
        Use this method to respond to such pre-checkout queries.

        Source: https://core.telegram.org/bots/api#answerprecheckoutquery

        :param pre_checkout_query_id: Unique identifier for the query to be answered
        :type pre_checkout_query_id: :obj:`base.String`
        :param ok: Specify True if everything is alright (goods are available, etc.) and the
            bot is ready to proceed with the order. Use False if there are any problems.
        :type ok: :obj:`base.Boolean`
        :param error_message: Required if ok is False
            Error message in human readable form that explains the reason for failure to proceed with the checkout
            (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling
            out your payment details. Please choose a different color or garment!").
            Telegram will display this message to the user.
        :type error_message: :obj:`typing.Union[base.String, None]`
        :return: On success, True is returned
        :rtype: :obj:`base.Boolean`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.ANSWER_PRE_CHECKOUT_QUERY, payload)
        return result

    # === Games ===
    # https://core.telegram.org/bots/api#games

    async def set_passport_data_errors(self,
                                       user_id: base.Integer,
                                       errors: typing.List[types.PassportElementError]) -> base.Boolean:
        """
        Informs a user that some of the Telegram Passport elements they provided contains errors.
        The user will not be able to re-submit their Passport to you until the errors are fixed
        (the contents of the field for which you returned the error must change).
        Returns True on success.

        Use this if the data submitted by the user doesn't satisfy the standards your service
        requires for any reason. For example, if a birthday date seems invalid, a submitted document
        is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message
        to make sure the user knows how to correct the issues.

        Source https://core.telegram.org/bots/api#setpassportdataerrors

        :param user_id: User identifier
        :type user_id: :obj:`base.Integer`
        :param errors: A JSON-serialized array describing the errors
        :type errors: :obj:`typing.List[types.PassportElementError]`
        :return: Returns True on success
        :rtype: :obj:`base.Boolean`
        """
        errors = prepare_arg(errors)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SET_PASSPORT_DATA_ERRORS, payload)
        return result

    # === Games ===
    # https://core.telegram.org/bots/api#games

    async def send_game(self, chat_id: base.Integer, game_short_name: base.String,
                        disable_notification: typing.Union[base.Boolean, None] = None,
                        reply_to_message_id: typing.Union[base.Integer, None] = None,
                        reply_markup: typing.Union[types.InlineKeyboardMarkup, None] = None) -> types.Message:
        """
        Use this method to send a game.

        Source: https://core.telegram.org/bots/api#sendgame

        :param chat_id: Unique identifier for the target chat
        :type chat_id: :obj:`base.Integer`
        :param game_short_name: Short name of the game, serves as the unique identifier for the game. \
            Set up your games via Botfather.
        :type game_short_name: :obj:`base.String`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`typing.Union[base.Boolean, None]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Union[base.Integer, None]`
        :param reply_markup: A JSON-serialized object for an inline keyboard
            If empty, one ‘Play game_title’ button will be shown. If not empty, the first button must launch the game.
        :type reply_markup: :obj:`typing.Union[types.InlineKeyboardMarkup, None]`
        :return: On success, the sent Message is returned
        :rtype: :obj:`types.Message`
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SEND_GAME, payload)
        return types.Message(**result)

    async def set_game_score(self, user_id: base.Integer, score: base.Integer,
                             force: typing.Union[base.Boolean, None] = None,
                             disable_edit_message: typing.Union[base.Boolean, None] = None,
                             chat_id: typing.Union[base.Integer, None] = None,
                             message_id: typing.Union[base.Integer, None] = None,
                             inline_message_id: typing.Union[base.String,
                                                             None] = None) -> types.Message or base.Boolean:
        """
        Use this method to set the score of the specified user in a game.

        Source: https://core.telegram.org/bots/api#setgamescore

        :param user_id: User identifier
        :type user_id: :obj:`base.Integer`
        :param score: New score, must be non-negative
        :type score: :obj:`base.Integer`
        :param force: Pass True, if the high score is allowed to decrease
            This can be useful when fixing mistakes or banning cheaters
        :type force: :obj:`typing.Union[base.Boolean, None]`
        :param disable_edit_message: Pass True, if the game message should not be automatically
            edited to include the current scoreboard
        :type disable_edit_message: :obj:`typing.Union[base.Boolean, None]`
        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the target chat
        :type chat_id: :obj:`typing.Union[base.Integer, None]`
        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`typing.Union[base.Integer, None]`
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`typing.Union[base.String, None]`
        :return: On success, if the message was sent by the bot, returns the edited Message, otherwise returns True
            Returns an error, if the new score is not greater than the user's
            current score in the chat and force is False.
        :rtype: :obj:`typing.Union[types.Message, base.Boolean]`
        """
        payload = generate_payload(**locals())

        result = await self.request(api.Methods.SET_GAME_SCORE, payload)
        if isinstance(result, bool):
            return result
        return types.Message(**result)

    async def get_game_high_scores(self, user_id: base.Integer,
                                   chat_id: typing.Union[base.Integer, None] = None,
                                   message_id: typing.Union[base.Integer, None] = None,
                                   inline_message_id: typing.Union[base.String,
                                                                   None] = None) -> typing.List[types.GameHighScore]:
        """
        Use this method to get data for high score tables.

        This method will currently return scores for the target user, plus two of his closest neighbors on each side.
        Will also return the top three users if the user and his neighbors are not among them.
        Please note that this behavior is subject to change.

        Source: https://core.telegram.org/bots/api#getgamehighscores

        :param user_id: Target user id
        :type user_id: :obj:`base.Integer`
        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the target chat
        :type chat_id: :obj:`typing.Union[base.Integer, None]`
        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`typing.Union[base.Integer, None]`
        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`typing.Union[base.String, None]`
        :return: Will return the score of the specified user and several of his neighbors in a game
            On success, returns an Array of GameHighScore objects.
            This method will currently return scores for the target user,
            plus two of his closest neighbors on each side. Will also return the top three users if the
            user and his neighbors are not among them.
        :rtype: :obj:`typing.List[types.GameHighScore]`
        """
        payload = generate_payload(**locals())
        result = await self.request(api.Methods.GET_GAME_HIGH_SCORES, payload)

        return [types.GameHighScore(**gamehighscore) for gamehighscore in result]
