import asyncio
import io
from typing import Union, TypeVar, List, Dict, Optional

import aiohttp

from . import api
from .. import types
from ..utils import json
from ..utils.payload import generate_payload, prepare_arg

InputFile = TypeVar('InputFile', io.BytesIO, io.FileIO, str)
String = TypeVar('String', bound=str)
Integer = TypeVar('Integer', bound=int)
Float = TypeVar('Float', bound=float)
Boolean = TypeVar('Boolean', bound=bool)


class BaseBot:
    """
    Base class for bot. It's raw bot.
    """

    def __init__(self, token: String,
                 loop: Optional[Union[asyncio.BaseEventLoop, asyncio.AbstractEventLoop]] = None,
                 connections_limit: Optional[Integer] = 10, proxy=None, proxy_auth=None):
        """
        Instructions how to get Bot token is found here: https://core.telegram.org/bots#3-how-do-i-create-a-bot

        :param token: token from @BotFather
        :param loop: event loop
        :param connections_limit: connections limit for aiohttp.ClientSession
        """

        self.__token = token
        self.proxy = proxy
        self.proxy_auth = proxy_auth

        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=connections_limit),
            loop=self.loop, json_serialize=json.dumps)
        self._temp_sessions = []
        api.check_token(token)

    def __del__(self):
        """
        When bot object is deleting - need close all sessions

        :return:
        """
        for session in self._temp_sessions:
            if not session.closed:
                session.close()
        if self.session and not self.session.closed:
            self.session.close()

    def create_temp_session(self) -> aiohttp.ClientSession:
        """
        Create temporary session

        :return:
        """
        session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=1, force_close=True),
            loop=self.loop)
        self._temp_sessions.append(session)
        return session

    def destroy_temp_session(self, session: aiohttp.ClientSession):
        """
        Destroy temporary session

        :param session:
        :return:
        """
        if not session.closed:
            session.close()
        if session in self._temp_sessions:
            self._temp_sessions.remove(session)

    async def request(self, method: String,
                      data: Optional[Dict] = None,
                      files: Optional[Dict] = None) -> Union[List, Dict, Boolean]:
        """
        Make an request to Telegram Bot API

        https://core.telegram.org/bots/api#making-requests

        :param method: API method
        :param data: request parameters
        :param files: files
        :return: Union[List, Dict]
        :raise: :class:`aiogram.exceptions.TelegramApiError`
        """
        return await api.request(self.session, self.__token, method, data, files,
                                 proxy=self.proxy, proxy_auth=self.proxy_auth)

    async def download_file(self, file_path: String,
                            destination: Optional[InputFile] = None,
                            timeout: Optional[Integer] = 30,
                            chunk_size: Optional[Integer] = 65536,
                            seek: Optional[Boolean] = True) -> Union[io.BytesIO, io.FileIO]:
        """
        Download file by file_path to destination

        if You want to automatically create destination (:class:`io.BytesIO`) use default
            value of destination and handle result of this method.

        :param file_path: String
        :param destination: filename or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO`
        :param timeout: Integer
        :param chunk_size: Integer
        :param seek: Boolean - go to start of file when downloading is finished.
        :return: destination
        """
        if destination is None:
            destination = io.BytesIO()

        session = self.create_temp_session()
        url = api.FILE_URL.format(token=self.__token, path=file_path)

        dest = destination if isinstance(destination, io.IOBase) else open(destination, 'wb')
        try:
            async with session.get(url, timeout=timeout, proxy=self.proxy, proxy_auth=self.proxy_auth) as response:
                while True:
                    chunk = await response.content.read(chunk_size)
                    if not chunk:
                        break
                    dest.write(chunk)
                    dest.flush()
            if seek:
                dest.seek(0)
            return dest
        finally:
            self.destroy_temp_session(session)

    async def send_file(self, file_type, method, file, payload) -> Union[Dict, Boolean]:
        """
        Send file

        https://core.telegram.org/bots/api#inputfile

        :param file_type: field name
        :param method: API metod
        :param file: String or io.IOBase
        :param payload: request payload
        :return: resonse
        """
        if isinstance(file, str):
            # You can use file ID or URL in the most of requests
            payload[file_type] = file
            files = None
        elif isinstance(file, (io.IOBase, io.FileIO)):
            files = {file_type: file.read()}
        else:
            files = {file_type: file}

        return await self.request(method, payload, files)

    # === Getting updates ===
    # https://core.telegram.org/bots/api#getting-updates

    async def get_updates(self, offset: Optional[Integer] = None,
                          limit: Optional[Integer] = None,
                          timeout: Optional[Integer] = None,
                          allowed_updates: Optional[List[String]] = None) -> List[Dict]:
        """
        Use this method to receive incoming updates using long polling (wiki). An Array of Update objects is returned.

        Notes
            1. This method will not work if an outgoing webhook is set up.
            2. In order to avoid getting duplicate updates, recalculate offset after each server response.

        Source: https://core.telegram.org/bots/api#getupdates

        :param offset: Integer (Optional) - Identifier of the first update to be returned. Must be greater
            by one than the highest among the identifiers of previously received updates.
            By default, updates starting with the earliest unconfirmed update are returned.
            An update is considered confirmed as soon as getUpdates is called with an offset higher than its update_id.
            The negative offset can be specified to retrieve updates starting from -
            offset update from the end of the updates queue.
            All previous updates will forgotten.
        :param limit: Integer (Optional) - Limits the number of updates to be retrieved.
            Values between 1—100 are accepted. Defaults to 100.
        :param timeout: Integer (Optional) - Timeout in seconds for long polling.
            Defaults to 0, i.e. usual short polling.
            Should be positive, short polling should be used for testing purposes only.
        :param allowed_updates: List[String] (Optional) - List the types of updates you want your bot to receive.
            For example, specify [“message”, “edited_channel_post”, “callback_query”]
            to only receive updates of these types.
            See Update for a complete list of available update types.
            Specify an empty list to receive all updates regardless of type (default).
            If not specified, the previous setting will be used.

            Please note that this parameter doesn't affect updates created before the call to the getUpdates,
            so unwanted updates may be received for a short period of time.
        :return: An Array of Update objects is returned.
        """
        allowed_updates = prepare_arg(allowed_updates)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_UPDATES, payload)

    async def set_webhook(self, url: String, certificate: Optional[InputFile] = None,
                          max_connections: Optional[Integer] = None,
                          allowed_updates: Optional[List[String]] = None) -> Boolean:
        """
        Use this method to specify a url and receive incoming updates via an outgoing webhook.
            Whenever there is an update for the bot, we will send an HTTPS POST request to the specified url,
            containing a JSON-serialized Update. In case of an unsuccessful request,
            we will give up after a reasonable amount of attempts. Returns true.

        If you'd like to make sure that the Webhook request comes from Telegram,
            we recommend using a secret path in the URL, e.g. https://www.example.com/<token>.
            Since nobody else knows your bot‘s token, you can be pretty sure it’s us.

        Notes
            1. You will not be able to receive updates using getUpdates for as long as an outgoing webhook
            is set up.
            2. To use a self-signed certificate, you need to upload your public key certificate
                using certificate parameter. Please upload as InputFile, sending a String will not work.
            3. Ports currently supported for Webhooks: 443, 80, 88, 8443.
            NEW! If you're having any trouble setting up webhooks, please check out this amazing guide to
            Webhooks.

        Source: https://core.telegram.org/bots/api#setwebhook

        :param url: String - HTTPS url to send updates to. Use an empty string to remove webhook integration
        :param certificate: InputFile (Optional) - Upload your public key certificate so that the root
            certificate in use can be checked. See our self-signed guide for details.
        :param max_connections: Integer (Optional) - Maximum allowed number of simultaneous HTTPS connections
            to the webhook for update delivery, 1-100. Defaults to 40. Use lower values to limit the load
            on your bot‘s server, and higher values to increase your bot’s throughput.
        :param allowed_updates: List[String] (Optional) - List the types of updates you want your bot to receive.
        For example, specify [“message”, “edited_channel_post”, “callback_query”]
        to only receive updates of these types. See Update for a complete list of available update types.
        Specify an empty list to receive all updates regardless of type (default).
        If not specified, the previous setting will be used.
        Please note that this parameter doesn't affect updates created before the call to the setWebhook,
        so unwanted updates may be received for a short period of time.
        :return: Returns true.
        """
        allowed_updates = prepare_arg(allowed_updates)
        payload = generate_payload(**locals(), exclude=['certificate'])

        return await self.send_file('certificate', api.Methods.SET_WEBHOOK, certificate, payload)

    async def delete_webhook(self) -> Boolean:
        """
        Use this method to remove webhook integration if you decide to switch back to getUpdates.
            Returns True on success. Requires no parameters.

        Source: https://core.telegram.org/bots/api#deletewebhook

        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.DELETE_WEBHOOK, payload)

    async def get_webhook_info(self) -> Dict:
        """
        Use this method to get current webhook status. Requires no parameters. On success,
            returns a WebhookInfo object. If the bot is using getUpdates, will return an object
            with the url field empty.

        Source: https://core.telegram.org/bots/api#getwebhookinfo

        :return: On success, returns a WebhookInfo object.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_WEBHOOK_INFO, payload)

    # === Base methods ===
    # https://core.telegram.org/bots/api#available-methods

    async def get_me(self) -> Dict:
        """
        A simple method for testing your bot's auth token. Requires no parameters.
            Returns basic information about the bot in form of a User object.

        Source: https://core.telegram.org/bots/api#getme

        :return: Returns basic information about the bot in form of a User object.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_ME, payload)

    async def send_message(self, chat_id: Union[Integer, String],
                           text: String, parse_mode: Optional[String] = None,
                           disable_web_page_preview: Optional[Boolean] = None,
                           disable_notification: Optional[Boolean] = None,
                           reply_to_message_id: Optional[Integer] = None,
                           reply_markup: Optional[Union[
                               types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send text messages. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendmessage

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param text: String - Text of the message to be sent
        :param parse_mode: String (Optional) - Send Markdown or HTML, if you want Telegram apps to show bold,
            italic, fixed-width text or inline URLs in your bot's message.
        :param disable_web_page_preview: Boolean (Optional) - Disables link previews for links in this message
        :param disable_notification: Boolean (Optional) - Sends the message silently. Users will receive
            a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SEND_MESSAGE, payload)

    async def forward_message(self, chat_id: Union[Integer, String],
                              from_chat_id: Union[Integer, String],
                              message_id: Integer,
                              disable_notification: Optional[Boolean] = None) -> Dict:
        """
        Use this method to forward messages of any kind. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#forwardmessage

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of the
            target channel (in the format @channelusername)
        :param from_chat_id: Union[Integer, String] - Unique identifier for the chat where the original
            message was sent (or channel username in the format @channelusername)
        :param disable_notification: Boolean (Optional) - Sends the message silently. Users will receive a
            notification with no sound.
        :param message_id: Integer - Message identifier in the chat specified in from_chat_id
        :return: On success, the sent Message is returned.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.FORWARD_MESSAGE, payload)

    async def send_photo(self, chat_id: Union[Integer, String],
                         photo: Union[io.BytesIO, io.FileIO, String],
                         caption: Optional[String] = None,
                         disable_notification: Optional[Boolean] = None,
                         reply_to_message_id: Optional[Integer] = None,
                         reply_markup: Optional[Union[
                             types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send photos. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendphoto

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of
            the target channel (in the format @channelusername)
        :param photo: Union[io.BytesIO, io.FileIO, String] - Photo to send. Pass a file_id as String to send
            a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for
            Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data.
        :param caption: String (Optional) - Photo caption (may also be used when resending photos by file_id),
            0-200 characters
        :param disable_notification: Boolean (Optional) - Sends the message silently. Users will receive
            a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['photo'])

        return await self.send_file('photo', api.Methods.SEND_PHOTO, photo, payload)

    async def send_audio(self, chat_id: Union[Integer, String],
                         audio: Union[io.BytesIO, io.FileIO, String],
                         caption: Optional[String] = None,
                         duration: Optional[Integer] = None,
                         performer: Optional[String] = None,
                         title: Optional[String] = None,
                         disable_notification: Optional[Boolean] = None,
                         reply_to_message_id: Optional[Integer] = None,
                         reply_markup: Optional[Union[
                             types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player.
            Your audio must be in the .mp3 format. On success, the sent Message is returned.
            Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.

        For sending voice messages, use the sendVoice method instead.

        Source: https://core.telegram.org/bots/api#sendaudio

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param audio: Union[io.BytesIO, io.FileIO, String] - Audio file to send. Pass a file_id as String
            to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL
            as a String for Telegram to get an audio file from the Internet, or upload a new one
            using multipart/form-data.
        :param caption: String (Optional) - Audio caption, 0-200 characters
        :param duration: Integer (Optional) - Duration of the audio in seconds
        :param performer: String (Optional) - Performer
        :param title: String (Optional) - Track name
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['audio'])

        return await self.send_file('audio', api.Methods.SEND_AUDIO, audio, payload)

    async def send_document(self, chat_id: Union[Integer, String],
                            document: Union[io.BytesIO, io.FileIO, String],
                            caption: Optional[String] = None,
                            disable_notification: Optional[Boolean] = None,
                            reply_to_message_id: Optional[Integer] = None,
                            reply_markup: Optional[Union[
                                types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send general files. On success, the sent Message is returned.
            Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#senddocument

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param document: Union[io.BytesIO, io.FileIO, String] - File to send. Pass a file_id as String
            to send a file that exists on the Telegram servers (recommended), pass an HTTP URL
            as a String for Telegram to get a file from the Internet, or upload a new one
            using multipart/form-data.
        :param caption: String (Optional) - Document caption
            (may also be used when resending documents by file_id), 0-200 characters
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['document'])

        return await self.send_file('document', api.Methods.SEND_DOCUMENT, document, payload)

    async def send_video(self, chat_id: Union[Integer, String],
                         video: Union[io.BytesIO, io.FileIO, String],
                         duration: Optional[Integer] = None,
                         width: Optional[Integer] = None,
                         height: Optional[Integer] = None,
                         caption: Optional[String] = None,
                         disable_notification: Optional[Boolean] = None,
                         reply_to_message_id: Optional[Integer] = None,
                         reply_markup: Optional[Union[
                             types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send video files, Telegram clients support mp4 videos
            (other formats may be sent as Document). On success, the sent Message is returned.
            Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvideo

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param video: Union[io.BytesIO, io.FileIO, String] - Video to send. Pass a file_id as String
            to send a video that exists on the Telegram servers (recommended), pass an HTTP URL
            as a String for Telegram to get a video from the Internet, or upload a new video
            using multipart/form-data.
        :param duration: Integer (Optional) - Duration of sent video in seconds
        :param width: Integer (Optional) - Video width
        :param height: Integer (Optional) - Video height
        :param caption: String (Optional) - Video caption (may also be used when resending videos by file_id),
            0-200 characters
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['video'])

        return await self.send_file('video', api.Methods.SEND_VIDEO, video, payload)

    async def send_voice(self, chat_id: Union[Integer, String],
                         voice: Union[io.BytesIO, io.FileIO, String],
                         caption: Optional[String] = None,
                         duration: Optional[Integer] = None,
                         disable_notification: Optional[Boolean] = None,
                         reply_to_message_id: Optional[Integer] = None,
                         reply_markup: Optional[Union[
                             types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send audio files, if you want Telegram clients to display the file
            as a playable voice message. For this to work, your audio must be in an .ogg file encoded with OPUS
            (other formats may be sent as Audio or Document). On success, the sent Message is returned.
            Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvoice

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param voice: Union[io.BytesIO, io.FileIO, String] - Audio file to send. Pass a file_id as String
            to send a file that exists on the Telegram servers (recommended), pass an HTTP URL
            as a String for Telegram to get a file from the Internet, or upload a new one
            using multipart/form-data.
        :param caption: String (Optional) - Voice message caption, 0-200 characters
        :param duration: Integer (Optional) - Duration of the voice message in seconds
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard,
            instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['voice'])

        return await self.send_file('voice', api.Methods.SEND_VOICE, voice, payload)

    async def send_video_note(self, chat_id: Union[Integer, String],
                              video_note: Union[io.BytesIO, io.FileIO, String],
                              duration: Optional[Integer] = None,
                              length: Optional[Integer] = None,
                              disable_notification: Optional[Boolean] = None,
                              reply_to_message_id: Optional[Integer] = None,
                              reply_markup: Optional[Union[
                                  types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long. Use this method
            to send video messages. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendvideonote

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param video_note: Union[io.BytesIO, io.FileIO, String] - Video note to send. Pass a file_id
            as String to send a video note that exists on the Telegram servers (recommended)
            or upload a new video using multipart/form-data. Sending video notes by a URL is currently unsupported
        :param duration: Integer (Optional) - Duration of sent video in seconds
        :param length: Integer (Optional) - Video width and height
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['video_note'])

        return await self.send_file('video_note', api.Methods.SEND_VIDEO_NOTE, video_note, payload)

    async def send_location(self, chat_id: Union[Integer, String],
                            latitude: Float, longitude: Float,
                            disable_notification: Optional[Boolean] = None,
                            reply_to_message_id: Optional[Integer] = None,
                            reply_markup: Optional[Union[
                                types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send point on the map. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendlocation

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param latitude: Float - Latitude of location
        :param longitude: Float - Longitude of location
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SEND_LOCATION, payload)

    async def send_venue(self, chat_id: Union[Integer, String],
                         latitude: Float,
                         longitude: Float,
                         title: String,
                         address: String,
                         foursquare_id: Optional[String] = None,
                         disable_notification: Optional[Boolean] = None,
                         reply_to_message_id: Optional[Integer] = None,
                         reply_markup: Optional[Union[
                             types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send information about a venue. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendvenue

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param latitude: Float - Latitude of the venue
        :param longitude: Float - Longitude of the venue
        :param title: String - Name of the venue
        :param address: String - Address of the venue
        :param foursquare_id: String (Optional) - Foursquare identifier of the venue
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SEND_VENUE, payload)

    async def send_contact(self, chat_id: Union[Integer, String],
                           phone_number: String,
                           first_name: String,
                           last_name: Optional[String] = None,
                           disable_notification: Optional[Boolean] = None,
                           reply_to_message_id: Optional[Integer] = None,
                           reply_markup: Optional[Union[
                               types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send phone contacts. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendcontact

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or
            username of the target channel (in the format @channelusername)
        :param phone_number: String - Contact's phone number
        :param first_name: String - Contact's first name
        :param last_name: String (Optional) - Contact's last name
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SEND_CONTACT, payload)

    async def send_chat_action(self, chat_id: Union[Integer, String], action: String) -> Boolean:
        """
        Use this method when you need to tell the user that something is happening on the bot's side.
            The status is set for 5 seconds or less (when a message arrives from your bot,
            Telegram clients clear its typing status). Returns True on success.

        Example: The ImageBot needs some time to process a request and upload the image.
            Instead of sending a text message along the lines of “Retrieving image, please wait…”,
            the bot may use sendChatAction with action = upload_photo. The user will
            see a “sending photo” status for the bot.

        We only recommend using this method when a response from the bot will take a noticeable amount
            of time to arrive.

        Source: https://core.telegram.org/bots/api#sendchataction

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param action: String - Type of action to broadcast. Choose one, depending on what the user is about to receive:
            typing for text messages, upload_photo for photos, record_video or upload_video for videos,
            record_audio or upload_audio for audio files, upload_document for general files,
            find_location for location data, record_video_note or upload_video_note for video notes.
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SEND_CHAT_ACTION, payload)

    async def get_user_profile_photos(self, user_id: Integer,
                                      offset: Optional[Integer] = None,
                                      limit: Optional[Integer] = None) -> Dict:
        """
        Use this method to get a list of profile pictures for a user. Returns a UserProfilePhotos object.

        Source: https://core.telegram.org/bots/api#getuserprofilephotos

        :param user_id: Integer - Unique identifier of the target user
        :param offset: Integer (Optional) - Sequential number of the first photo to be returned.
            By default, all photos are returned.
        :param limit: Integer (Optional) - Limits the number of photos to be retrieved.
            Values between 1—100 are accepted. Defaults to 100.
        :return: Returns a UserProfilePhotos object.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_USER_PROFILE_PHOTOS, payload)

    async def get_file(self, file_id: String) -> Dict:
        """
        Use this method to get basic info about a file and prepare it for downloading.
            For the moment, bots can download files of up to 20MB in size. On success, a File object is returned.
            The file can then be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>,
            where <file_path> is taken from the response. It is guaranteed that the link
            will be valid for at least 1 hour. When the link expires,
            a new one can be requested by calling getFile again.

        Note: This function may not preserve the original file name and MIME type.
            You should save the file's MIME type and name (if available) when the File object is received.

        Source: https://core.telegram.org/bots/api#getfile

        :param file_id: String - File identifier to get info about
        :return: On success, a File object is returned.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_FILE, payload)

    async def kick_chat_member(self, chat_id: Union[Integer, String], user_id: Integer, until_date: Integer) -> Boolean:
        """
        Use this method to kick a user from a group, a supergroup or a channel.
            In the case of supergroups and channels, the user will not be able to return to the group on their
            own using invite links, etc., unless unbanned first. The bot must be an administrator in the chat
            for this to work and must have the appropriate admin rights. Returns True on success.

        Note: In regular groups (non-supergroups), this method will only work
            if the ‘All Members Are Admins’ setting is off in the target group.
            Otherwise members may only be removed by the group's creator or by the member that added them.

        Source: https://core.telegram.org/bots/api#kickchatmember

        :param chat_id: Union[Integer, String] - Unique identifier for the target group or username
            of the target supergroup or channel (in the format @channelusername)
        :param user_id: Integer - Unique identifier of the target user
        :param until_date: Integer - Date when the user will be unbanned, unix time. If user is banned for
            more than 366 days or less than 30 seconds from the current time they are considered to be banned forever
        :return: In the case of supergroups and channels, the user will not be able to return to the
            group on their own using invite links, etc.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.KICK_CHAT_MEMBER, payload)

    async def unban_chat_member(self, chat_id: Union[Integer, String], user_id: Integer) -> Boolean:
        """
        Use this method to unban a previously kicked user in a supergroup or channel.
            The user will not return to the group or channel automatically, but will be able to join via link, etc.
            The bot must be an administrator for this to work. Returns True on success.

        Source: https://core.telegram.org/bots/api#unbanchatmember

        :param chat_id: Union[Integer, String] - Unique identifier for the target group or
            username of the target supergroup or channel (in the format @username)
        :param user_id: Integer - Unique identifier of the target user
        :return: The user will not return to the group or channel automatically,
            but will be able to join via link, etc.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.UNBAN_CHAT_MEMBER, payload)

    async def restrict_chat_member(self, chat_id: Union[Integer, String],
                                   user_id: Integer,
                                   until_date: Integer,
                                   can_send_messages: Boolean,
                                   can_send_media_messages: Boolean,
                                   can_send_other_messages: Boolean,
                                   can_add_web_page_previews: Boolean) -> Boolean:
        """
        Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup
            for this to work and must have the appropriate admin rights. Pass True for all Booleanean
            parameters to lift restrictions from a user. Returns True on success.

        Source: https://core.telegram.org/bots/api#restrictchatmember

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat
            or username of the target supergroup (in the format @supergroupusername)
        :param user_id: Integer - Unique identifier of the target user
        :param until_date: Integer - Date when restrictions will be lifted for the user, unix time.
            If user is restricted for more than 366 days or less than 30 seconds from the current time,
            they are considered to be restricted forever
        :param can_send_messages: Boolean - Pass True, if the user can send text messages, contacts,
            locations and venues
        :param can_send_media_messages: Boolean - Pass True, if the user can send audios, documents,
            photos, videos, video notes and voice notes, implies can_send_messages
        :param can_send_other_messages: Boolean - Pass True, if the user can send animations, games,
            stickers and use inline bots, implies can_send_media_messages
        :param can_add_web_page_previews: Boolean - Pass True, if the user may add web page previews
            to their messages, implies can_send_media_messages
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.RESTRICT_CHAT_MEMBER, payload)

    async def promote_chat_member(self, chat_id: Union[Integer, String],
                                  user_id: Integer,
                                  can_change_info: Boolean,
                                  can_post_messages: Boolean,
                                  can_edit_messages: Boolean,
                                  can_delete_messages: Boolean,
                                  can_invite_users: Boolean,
                                  can_restrict_members: Boolean,
                                  can_pin_messages: Boolean,
                                  can_promote_members: Boolean) -> Boolean:
        """
        Use this method to promote or demote a user in a supergroup or a channel.
            The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
            Pass False for all Booleanean parameters to demote a user. Returns True on success.

        Source: https://core.telegram.org/bots/api#promotechatmember

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat
            or username of the target channel (in the format @channelusername)
        :param user_id: Integer - Unique identifier of the target user
        :param can_change_info: Boolean - Pass True, if the administrator can change chat title,
            photo and other settings
        :param can_post_messages: Boolean - Pass True, if the administrator can create channel posts, channels only
        :param can_edit_messages: Boolean - Pass True, if the administrator can edit messages of other users,
            channels only
        :param can_delete_messages: Boolean - Pass True, if the administrator can delete messages of other users
        :param can_invite_users: Boolean - Pass True, if the administrator can invite new users to the chat
        :param can_restrict_members: Boolean - Pass True, if the administrator can restrict, ban or unban chat members
        :param can_pin_messages: Boolean - Pass True, if the administrator can pin messages, supergroups only
        :param can_promote_members: Boolean - Pass True, if the administrator can add new administrators
            with a subset of his own privileges or demote administrators that he has promoted,
            directly or indirectly (promoted by administrators that were appointed by him)
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.PROMOTE_CHAT_MEMBER, payload)

    async def export_chat_invite_link(self, chat_id: Union[Integer, String]) -> String:
        """
        Use this method to export an invite link to a supergroup or a channel.
            The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
            Returns exported invite link as String on success.

        Source: https://core.telegram.org/bots/api#exportchatinvitelink

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :return: Returns exported invite link as String on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.EXPORT_CHAT_INVITE_LINK, payload)

    async def set_chat_photo(self, chat_id: Union[Integer, String], photo: io.BytesIO) -> Boolean:
        """
        Use this method to set a new profile photo for the chat. Photos can't be changed for private chats.
            The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
            Returns True on success.

        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
            setting is off in the target group.

        Source: https://core.telegram.org/bots/api#setchatphoto

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
        of the target channel (in the format @channelusername)
        :param photo: io.BytesIO - New chat photo, uploaded using multipart/form-data
        :return: Returns True on success.
        """
        payload = generate_payload(**locals(), exclude=['photo'])

        return await self.send_file('photo', api.Methods.SET_CHAT_PHOTO, photo, payload)

    async def delete_chat_photo(self, chat_id: Union[Integer, String]) -> Boolean:
        """
        Use this method to delete a chat photo. Photos can't be changed for private chats.
            The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
            Returns True on success.

        Note: In regular groups (non-supergroups), this method will only work if the
            ‘All Members Are Admins’ setting is off in the target group.

        Source: https://core.telegram.org/bots/api#deletechatphoto

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat
            or username of the target channel (in the format @channelusername)
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.DELETE_CHAT_PHOTO, payload)

    async def set_chat_title(self, chat_id: Union[Integer, String], title: String) -> Boolean:
        """
        Use this method to change the title of a chat. Titles can't be changed for private chats.
            The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
            Returns True on success.

        Note: In regular groups (non-supergroups), this method will only work if the
            ‘All Members Are Admins’ setting is off in the target group.

        Source: https://core.telegram.org/bots/api#setchattitle

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param title: String - New chat title, 1-255 characters
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SET_CHAT_TITLE, payload)

    async def set_chat_description(self, chat_id: Union[Integer, String], description: String) -> Boolean:
        """
        Use this method to change the description of a supergroup or a channel.
            The bot must be an administrator in the chat for this to work and must have the
            appropriate admin rights. Returns True on success.

        Source: https://core.telegram.org/bots/api#setchatdescription

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat
            or username of the target channel (in the format @channelusername)
        :param description: String - New chat description, 0-255 characters
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SET_CHAT_DESCRIPTION, payload)

    async def pin_chat_message(self, chat_id: Union[Integer, String], message_id: Integer,
                               disable_notification: Boolean) -> Boolean:
        """
        Use this method to pin a message in a supergroup. The bot must be an administrator in the chat
            for this to work and must have the appropriate admin rights. Returns True on success.

        Source: https://core.telegram.org/bots/api#pinchatmessage

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat
            or username of the target supergroup (in the format @supergroupusername)
        :param message_id: Integer - Identifier of a message to pin
        :param disable_notification: Boolean - Pass True, if it is not necessary to send a notification
            to all group members about the new pinned message
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.PIN_CHAT_MESSAGE, payload)

    async def unpin_chat_message(self, chat_id: Union[Integer, String]) -> Boolean:
        """
        Use this method to unpin a message in a supergroup chat. The bot must be an administrator
            in the chat for this to work and must have the appropriate admin rights. Returns True on success.

        Source: https://core.telegram.org/bots/api#unpinchatmessage

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or
            username of the target supergroup (in the format @supergroupusername)
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.UNPIN_CHAT_MESSAGE, payload)

    async def leave_chat(self, chat_id: Union[Integer, String]) -> Boolean:
        """
        Use this method for your bot to leave a group, supergroup or channel. Returns True on success.

        Source: https://core.telegram.org/bots/api#leavechat

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat
            or username of the target supergroup or channel (in the format @channelusername)
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.LEAVE_CHAT, payload)

    async def get_chat(self, chat_id: Union[Integer, String]) -> Dict:
        """
        Use this method to get up to date information about the chat
            (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.).
            Returns a Chat object on success.

        Source: https://core.telegram.org/bots/api#getchat

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of the
            target supergroup or channel (in the format @channelusername)
        :return: Returns a Chat object on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_CHAT, payload)

    async def get_chat_administrators(self, chat_id: Union[Integer, String]) -> List[Dict]:
        """
        Use this method to get a list of administrators in a chat. On success, returns an Array of ChatMember
            objects that contains information about all chat administrators except other bots.
            If the chat is a group or a supergroup and no administrators were appointed,
            only the creator will be returned.

        Source: https://core.telegram.org/bots/api#getchatadministrators

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of
            the target supergroup or channel (in the format @channelusername)
        :return: On success, returns an Array of ChatMember objects that contains information about all
            chat administrators except other bots.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_CHAT_ADMINISTRATORS, payload)

    async def get_chat_members_count(self, chat_id: Union[Integer, String]) -> Integer:
        """
        Use this method to get the number of members in a chat. Returns Int on success.

        Source: https://core.telegram.org/bots/api#getchatmemberscount

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of the target
            supergroup or channel (in the format @channelusername)
        :return: Returns Int on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_CHAT_MEMBERS_COUNT, payload)

    async def get_chat_member(self, chat_id: Union[Integer, String], user_id: Integer) -> Dict:
        """
        Use this method to get information about a member of a chat. Returns a ChatMember object on success.

        Source: https://core.telegram.org/bots/api#getchatmember

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target supergroup or channel (in the format @channelusername)
        :param user_id: Integer - Unique identifier of the target user
        :return: Returns a ChatMember object on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_CHAT_MEMBER, payload)

    async def answer_callback_query(self, callback_query_id: String,
                                    text: Optional[String] = None,
                                    show_alert: Optional[Boolean] = None,
                                    url: Optional[String] = None,
                                    cache_time: Optional[Integer] = None) -> Boolean:
        """
        Use this method to send answers to callback queries sent from inline keyboards.
            The answer will be displayed to the user as a notification at the top of the chat screen or as an alert.
            On success, True is returned.

        Alternatively, the user can be redirected to the specified Game URL. For this option to work,
            you must first create a game for your bot via BotFather and accept the terms.
            Otherwise, you may use links like t.me/your_bot?start=XXXX that open your bot with a parameter.

        Source: https://core.telegram.org/bots/api#answercallbackquery

        :param callback_query_id: String - Unique identifier for the query to be answered
        :param text: String (Optional) - Text of the notification. If not specified, nothing will be shown to the user,
            0-200 characters
        :param show_alert: Boolean (Optional) - If true, an alert will be shown by the client instead
            of a notification at the top of the chat screen. Defaults to false.
        :param url: String (Optional) - URL that will be opened by the user's client.
            If you have created a Game and accepted the conditions via @Botfather,
            specify the URL that opens your game – note that this will only work
            if the query comes from a callback_game button.

    Otherwise, you may use links like t.me/your_bot?start=XXXX that open your bot with a parameter.
        :param cache_time: Integer (Optional) - The maximum amount of time in seconds that the result
            of the callback query may be cached client-side. Telegram apps will support
            caching starting in version 3.14. Defaults to 0.
        :return: On success, True is returned.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.ANSWER_CALLBACK_QUERY, payload)

    # === Updating messages ===
    # https://core.telegram.org/bots/api#updating-messages

    async def edit_message_text(self, text: String,
                                chat_id: Optional[Union[Integer, String]] = None,
                                message_id: Optional[Integer] = None,
                                inline_message_id: Optional[String] = None,
                                parse_mode: Optional[String] = None,
                                disable_web_page_preview: Optional[Boolean] = None,
                                reply_markup: Optional[types.InlineKeyboardMarkup] = None) -> Boolean:
        """
        Use this method to edit text and game messages sent by the bot or via the bot (for inline bots).
            On success, if edited message is sent by the bot, the edited Message is returned,
            otherwise True is returned.

        Source: https://core.telegram.org/bots/api#editmessagetext

        :param chat_id: Union[Integer, String] (Optional) - Required if inline_message_id
            is not specified. Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param message_id: Integer (Optional) - Required if inline_message_id is not specified.
            Identifier of the sent message
        :param inline_message_id: String (Optional) - Required if chat_id and message_id are not specified.
            Identifier of the inline message
        :param text: String - New text of the message
        :param parse_mode: String (Optional) - Send Markdown or HTML, if you want Telegram apps to show bold,
            italic, fixed-width text or inline URLs in your bot's message.
        :param disable_web_page_preview: Boolean (Optional) - Disables link previews for links in this message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for
            an inline keyboard.
        :return: On success, if edited message is sent by the bot, the edited Message is returned,
            otherwise True is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.EDIT_MESSAGE_TEXT, payload)

    async def edit_message_caption(self, chat_id: Optional[Union[Integer, String]] = None,
                                   message_id: Optional[Integer] = None,
                                   inline_message_id: Optional[String] = None,
                                   caption: Optional[String] = None,
                                   reply_markup: Optional[types.InlineKeyboardMarkup] = None) -> Boolean:
        """
        Use this method to edit captions of messages sent by the bot or via the bot (for inline bots).
            On success, if edited message is sent by the bot, the edited Message is returned,
            otherwise True is returned.

        Source: https://core.telegram.org/bots/api#editmessagecaption

        :param chat_id: Union[Integer, String] (Optional) - Required if inline_message_id
            is not specified. Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param message_id: Integer (Optional) - Required if inline_message_id is not specified.
            Identifier of the sent message
        :param inline_message_id: String (Optional) - Required if chat_id and message_id are not specified.
            Identifier of the inline message
        :param caption: String (Optional) - New caption of the message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for an inline keyboard.
        :return: On success, if edited message is sent by the bot, the edited Message is returned,
            otherwise True is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.EDIT_MESSAGE_CAPTION, payload)

    async def edit_message_reply_markup(self, chat_id: Optional[Union[Integer, String]] = None,
                                        message_id: Optional[Integer] = None,
                                        inline_message_id: Optional[String] = None,
                                        reply_markup: Optional[types.InlineKeyboardMarkup] = None) -> Boolean:
        """
        Use this method to edit only the reply markup of messages sent by the bot or via the bot (for inline bots).
            On success, if edited message is sent by the bot, the edited Message is returned,
            otherwise True is returned.

        Source: https://core.telegram.org/bots/api#editmessagereplymarkup

        :param chat_id: Union[Integer, String] (Optional) - Required if inline_message_id is not specified.
            Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :param message_id: Integer (Optional) - Required if inline_message_id is not specified.
            Identifier of the sent message
        :param inline_message_id: String (Optional) - Required if chat_id and message_id are not specified.
            Identifier of the inline message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for an inline keyboard.
        :return: On success, if edited message is sent by the bot, the edited Message is returned,
            otherwise True is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.EDIT_MESSAGE_REPLY_MARKUP, payload)

    async def delete_message(self, chat_id: Union[Integer, String], message_id: Integer) -> Boolean:
        """
        Use this method to delete a message, including service messages, with the following limitations:
            - A message can only be deleted if it was sent less than 48 hours ago.
            - Bots can delete outgoing messages in groups and supergroups.
            - Bots granted can_post_messages permissions can delete outgoing messages in channels.
            - If the bot is an administrator of a group, it can delete any message there.
            - If the bot has can_delete_messages permission in a supergroup or a channel,
            it can delete any message there.
            Returns True on success.

        The following methods and objects allow your bot to handle stickers and sticker sets.

        Source: https://core.telegram.org/bots/api#deletemessage

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param message_id: Integer - Identifier of the message to delete
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.DELETE_MESSAGE, payload)

    # === Stickers ===
    # https://core.telegram.org/bots/api#stickers

    async def send_sticker(self, chat_id: Union[Integer, String],
                           sticker: Union[io.BytesIO, io.FileIO, String],
                           disable_notification: Optional[Boolean] = None,
                           reply_to_message_id: Optional[Integer] = None,
                           reply_markup: Optional[
                               Union[types.InlineKeyboardMarkup,
                                     types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send .webp stickers. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendsticker

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param sticker: Union[io.BytesIO, io.FileIO, String] - Sticker to send. Pass a file_id
            as String to send a file that exists on the Telegram servers (recommended),
            pass an HTTP URL as a String for Telegram to get a .webp file from the Internet,
            or upload a new one using multipart/form-data. More info on Sending Files »
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional) -
            Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals(), exclude=['sticker'])

        return await self.send_file('sticker', api.Methods.SEND_STICKER, sticker, payload)

    async def get_sticker_set(self, name: String) -> Dict:
        """
        Use this method to get a sticker set. On success, a StickerSet object is returned.

        Source: https://core.telegram.org/bots/api#getstickerset

        :param name: String - Name of the sticker set
        :return: On success, a StickerSet object is returned.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_STICKER_SET, payload)

    async def upload_sticker_file(self, user_id: Integer, png_sticker: io.BytesIO) -> Dict:
        """
        Use this method to upload a .png file with a sticker for later use in createNewStickerSet and addStickerToSet
            methods (can be used multiple times). Returns the uploaded File on success.

        Source: https://core.telegram.org/bots/api#uploadstickerfile

        :param user_id: Integer - User identifier of sticker file owner
        :param png_sticker: io.BytesIO - Png image with the sticker, must be up to 512 kilobytes in size,
            dimensions must not exceed 512px, and either width or height must be exactly 512px.
        :return: Returns the uploaded File on success.
        """
        payload = generate_payload(**locals(), exclude=['png_sticker'])

        return await self.send_file('png_sticker', api.Methods.UPLOAD_STICKER_FILE, png_sticker, payload)

    async def create_new_sticker_set(self, user_id: Integer,
                                     name: String, title: String,
                                     png_sticker: Union[io.BytesIO, io.FileIO, String],
                                     emojis: String,
                                     contains_masks: Optional[Boolean] = None,
                                     mask_position: Optional[types.MaskPosition] = None) -> Boolean:
        """
        Use this method to create new sticker set owned by a user. The bot will be able to edit
            the created sticker set. Returns True on success.

        Source: https://core.telegram.org/bots/api#createnewstickerset

        :param user_id: Integer - User identifier of created sticker set owner
        :param name: String - Short name of sticker set, to be used in t.me/addstickers/ URLs (e.g., animals).
            Can contain only english letters, digits and underscores. Must begin with a letter,
            can't contain consecutive underscores and must end in “_by_<bot username>”. <bot_username>
            is case insensitive. 1-64 characters.
        :param title: String - Sticker set title, 1-64 characters
        :param png_sticker: Union[io.BytesIO, io.FileIO, String] - Png image with the sticker,
            must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width
            or height must be exactly 512px. Pass a file_id as a String to send a file that
            already exists on the Telegram servers, pass an HTTP URL
            as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        :param emojis: String - One or more emoji corresponding to the sticker
        :param contains_masks: Boolean (Optional) - Pass True, if a set of mask stickers should be created
        :param mask_position: types.MaskPosition (Optional) - Position where the mask should be placed on faces
        :return: Returns True on success.
        """
        mask_position = prepare_arg(mask_position)
        payload = generate_payload(**locals(), exclude=['png_sticker'])

        return await self.send_file('png_sticker', api.Methods.CREATE_NEW_STICKER_SET, png_sticker, payload)

    async def add_sticker_to_set(self, user_id: Integer,
                                 name: String,
                                 png_sticker: Union[io.BytesIO,
                                                    io.FileIO, String],
                                 emojis: String,
                                 mask_position: Optional[types.MaskPosition] = None) -> Boolean:
        """
        Use this method to add a new sticker to a set created by the bot. Returns True on success.

        Source: https://core.telegram.org/bots/api#addstickertoset

        :param user_id: Integer - User identifier of sticker set owner
        :param name: String - Sticker set name
        :param png_sticker: Union[io.BytesIO, io.FileIO, String] - Png image with the sticker,
            must be up to 512 kilobytes in size, dimensions must not exceed 512px,
            and either width or height must be exactly 512px. Pass a file_id as a String
            to send a file that already exists on the Telegram servers, pass an HTTP URL
            as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        :param emojis: String - One or more emoji corresponding to the sticker
        :param mask_position: types.MaskPosition (Optional) - Position where the mask should be placed on faces
        :return: Returns True on success.
        """
        mask_position = prepare_arg(mask_position)
        payload = generate_payload(**locals(), exclude=['png_sticker'])

        return await self.send_file('png_sticker', api.Methods.ADD_STICKER_TO_SET, png_sticker, payload)

    async def set_sticker_position_in_set(self, sticker: String, position: Integer) -> Boolean:
        """
        Use this method to move a sticker in a set created by the bot to a specific position.
            Returns True on success.

        Source: https://core.telegram.org/bots/api#setstickerpositioninset

        :param sticker: String - File identifier of the sticker
        :param position: Integer - New sticker position in the set, zero-based
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SET_STICKER_POSITION_IN_SET, payload)

    async def delete_sticker_from_set(self, sticker: String) -> Boolean:
        """
        Use this method to delete a sticker from a set created by the bot. Returns True on success.

        The following methods and objects allow your bot to work in inline mode.
            Please see our Introduction to Inline bots for more details.

        To enable this option, send the /setinline command to @BotFather and provide the placeholder
            text that the user will see in the input field after typing your bot’s name.

        Source: https://core.telegram.org/bots/api#deletestickerfromset

        :param sticker: String - File identifier of the sticker
        :return: Returns True on success.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.DELETE_STICKER_FROM_SET, payload)

    # === inline mode ===
    # https://core.telegram.org/bots/api#inline-mode

    async def answer_inline_query(self, inline_query_id: String,
                                  results: [types.InlineQueryResult],
                                  cache_time: Optional[Integer] = None,
                                  is_personal: Optional[Boolean] = None,
                                  next_offset: Optional[String] = None,
                                  switch_pm_text: Optional[String] = None,
                                  switch_pm_parameter: Optional[String] = None) -> Boolean:
        """
        Use this method to send answers to an inline query. On success, True is returned.
            No more than 50 results per query are allowed.

        Source: https://core.telegram.org/bots/api#answerinlinequery

        :param inline_query_id: String - Unique identifier for the answered query
        :param results: [types.InlineQueryResult] - A JSON-serialized array of results for the inline query
        :param cache_time: Integer (Optional) - The maximum amount of time in seconds that the result
            of the inline query may be cached on the server. Defaults to 300.
        :param is_personal: Boolean (Optional) - Pass True, if results may be cached on the server side
            only for the user that sent the query. By default, results may be returned
            to any user who sends the same query
        :param next_offset: String (Optional) - Pass the offset that a client should send in the
            next query with the same text to receive more results.
            Pass an empty string if there are no more results or if you don‘t support pagination.
            Offset length can’t exceed 64 bytes.
        :param switch_pm_text: String (Optional) - If passed, clients will display a button with specified text
            that switches the user to a private chat with the bot and sends the bot a start
            message with the parameter switch_pm_parameter
        :param switch_pm_parameter: String (Optional) - Deep-linking parameter for the /start message
            sent to the bot when user presses the switch button. 1-64 characters,
            only A-Z, a-z, 0-9, _ and - are allowed.
            Example: An inline bot that sends YouTube videos can ask the user to connect the bot to their
            YouTube account to adapt search results accordingly. To do this,
            it displays a ‘Connect your YouTube account’ button above the results, or even before showing any.
            The user presses the button, switches to a private chat with the bot and,
            in doing so, passes a start parameter that instructs the bot to return an oauth link.
            Once done, the bot can offer a switch_inline button so that the user can easily return
            to the chat where they wanted to use the bot's inline capabilities.
        :return: On success, True is returned.
        """
        results = prepare_arg(results)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.ANSWER_INLINE_QUERY, payload)

    # === Payments ===
    # https://core.telegram.org/bots/api#payments

    async def send_invoice(self, chat_id: Integer,
                           title: String,
                           description: String,
                           payload: String,
                           provider_token: String,
                           start_parameter: String,
                           currency: String,
                           prices: [types.LabeledPrice],
                           photo_url: Optional[String] = None,
                           photo_size: Optional[Integer] = None,
                           photo_width: Optional[Integer] = None,
                           photo_height: Optional[Integer] = None,
                           need_name: Optional[Boolean] = None,
                           need_phone_number: Optional[Boolean] = None,
                           need_email: Optional[Boolean] = None,
                           need_shipping_address: Optional[Boolean] = None,
                           is_flexible: Optional[Boolean] = None,
                           disable_notification: Optional[Boolean] = None,
                           reply_to_message_id: Optional[Integer] = None,
                           reply_markup: Optional[types.InlineKeyboardMarkup] = None) -> Dict:
        """
        Use this method to send invoices. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendinvoice

        :param chat_id: Integer - Unique identifier for the target private chat
        :param title: String - Product name, 1-32 characters
        :param description: String - Product description, 1-255 characters
        :param payload: String - Bot-defined invoice payload, 1-128 bytes.
            This will not be displayed to the user, use for your internal processes.
        :param provider_token: String - Payments provider token, obtained via Botfather
        :param start_parameter: String - Unique deep-linking parameter that can be used to
            generate this invoice when used as a start parameter
        :param currency: String - Three-letter ISO 4217 currency code, see more on currencies
        :param prices: [types.LabeledPrice] - Price breakdown, a list of components
            (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :param photo_url: String (Optional) - URL of the product photo for the invoice.
            Can be a photo of the goods or a marketing image for a service.
            People like it better when they see what they are paying for.
        :param photo_size: Integer (Optional) - Photo size
        :param photo_width: Integer (Optional) - Photo width
        :param photo_height: Integer (Optional) - Photo height
        :param need_name: Boolean (Optional) - Pass True, if you require the user's full name to complete the order
        :param need_phone_number: Boolean (Optional) - Pass True, if you require
            the user's phone number to complete the order
        :param need_email: Boolean (Optional) - Pass True, if you require the user's email to complete the order
        :param need_shipping_address: Boolean (Optional) - Pass True, if you require the user's
            shipping address to complete the order
        :param is_flexible: Boolean (Optional) - Pass True, if the final price depends on the shipping method
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for an inline keyboard.
            If empty, one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button.
        :return: On success, the sent Message is returned.
        """
        prices = prepare_arg(prices)
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SEND_INVOICE, payload)

    async def answer_shipping_query(self, shipping_query_id: String,
                                    ok: Boolean,
                                    shipping_options: Optional[List[types.ShippingOption]] = None,
                                    error_message: Optional[String] = None) -> Boolean:
        """
        If you sent an invoice requesting a shipping address and the parameter is_flexible was specified,
            the Bot API will send an Update with a shipping_query field to the bot.
            Use this method to reply to shipping queries. On success, True is returned.

        Source: https://core.telegram.org/bots/api#answershippingquery

        :param shipping_query_id: String - Unique identifier for the query to be answered
        :param ok: Boolean - Specify True if delivery to the specified address is possible and
            False if there are any problems (for example, if delivery to the specified address is not possible)
        :param shipping_options: [types.ShippingOption] (Optional) - Required if ok is True.
            A JSON-serialized array of available shipping options.
        :param error_message: String (Optional) - Required if ok is False.
            Error message in human readable form that explains why it is impossible to complete the order
            (e.g. "Sorry, delivery to your desired address is unavailable').
            Telegram will display this message to the user.
        :return: On success, True is returned.
        """
        shipping_options = prepare_arg(shipping_options)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.ANSWER_SHIPPING_QUERY, payload)

    async def answer_pre_checkout_query(self, pre_checkout_query_id: String,
                                        ok: Boolean,
                                        error_message: Optional[String] = None) -> Boolean:
        """
        Once the user has confirmed their payment and shipping details,
            the Bot API sends the final confirmation in the form of an Update with the field pre_checkout_query.
            Use this method to respond to such pre-checkout queries. On success, True is returned.

        Note: The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.

        Source: https://core.telegram.org/bots/api#answerprecheckoutquery

        :param pre_checkout_query_id: String - Unique identifier for the query to be answered
        :param ok: Boolean - Specify True if everything is alright (goods are available, etc.)
            and the bot is ready to proceed with the order. Use False if there are any problems.
        :param error_message: String (Optional) - Required if ok is False.
            Error message in human readable form that explains the reason for failure to proceed with the checkout
            (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy
            filling out your payment details. Please choose a different color or garment!").
            Telegram will display this message to the user.
        :return: On success, True is returned.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.ANSWER_PRE_CHECKOUT_QUERY, payload)

    # === Games ===
    # https://core.telegram.org/bots/api#games

    async def send_game(self, chat_id: Integer,
                        game_short_name: String,
                        disable_notification: Optional[Boolean] = None,
                        reply_to_message_id: Optional[Integer] = None,
                        reply_markup: Optional[types.InlineKeyboardMarkup] = None) -> Dict:
        """
        Use this method to send a game. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendgame

        :param chat_id: Integer - Unique identifier for the target chat
        :param game_short_name: String - Short name of the game, serves as the unique identifier for the game.
            Set up your games via Botfather.
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for an inline keyboard.
            If empty, one ‘Play game_title’ button will be shown. If not empty, the first button must launch the game.
        :return: On success, the sent Message is returned.
        """
        reply_markup = prepare_arg(reply_markup)
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SEND_GAME, payload)

    async def set_game_score(self, user_id: Integer,
                             score: Integer,
                             force: Optional[Boolean] = None,
                             disable_edit_message: Optional[Boolean] = None,
                             chat_id: Optional[Integer] = None,
                             message_id: Optional[Integer] = None,
                             inline_message_id: Optional[String] = None) -> Union[types.Message, Boolean]:
        """
        Use this method to set the score of the specified user in a game. On success,
            if the message was sent by the bot, returns the edited Message, otherwise returns True.
            Returns an error, if the new score is not greater than the user's current
            score in the chat and force is False.

        Source: https://core.telegram.org/bots/api#setgamescore

        :param user_id: Integer - User identifier
        :param score: Integer - New score, must be non-negative
        :param force: Boolean (Optional) - Pass True, if the high score is allowed to decrease.
            This can be useful when fixing mistakes or banning cheaters
        :param disable_edit_message: Boolean (Optional) - Pass True, if the game message should not be
            automatically edited to include the current scoreboard
        :param chat_id: Integer (Optional) - Required if inline_message_id is not specified.
            Unique identifier for the target chat
        :param message_id: Integer (Optional) - Required if inline_message_id is not specified.
            Identifier of the sent message
        :param inline_message_id: String (Optional) - Required if chat_id and message_id are not specified.
            Identifier of the inline message
        :return: On success, if the message was sent by the bot, returns the edited Message, otherwise returns True.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SET_GAME_SCORE, payload)

    async def get_game_high_scores(self, user_id: Integer, chat_id: Optional[Integer] = None,
                                   message_id: Optional[Integer] = None,
                                   inline_message_id: Optional[String] = None) -> Integer:
        """
        Use this method to get data for high score tables. Will return the score of the specified
            user and several of his neighbors in a game. On success, returns an Array of GameHighScore objects.

        This method will currently return scores for the target user, plus two of his closest
            neighbors on each side. Will also return the top three users if the user and his
            neighbors are not among them. Please note that this behavior is subject to change.

        Source: https://core.telegram.org/bots/api#getgamehighscores

        :param user_id: Integer - Target user id
        :param chat_id: Integer (Optional) - Required if inline_message_id is not specified.
            Unique identifier for the target chat
        :param message_id: Integer (Optional) - Required if inline_message_id is not specified.
            Identifier of the sent message
        :param inline_message_id: String (Optional) - Required if chat_id and message_id are not specified.
            Identifier of the inline message
        :return: Will return the score of the specified user and several of his neighbors in a game.
        """
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_GAME_HIGH_SCORES, payload)
