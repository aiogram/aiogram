import datetime
import typing
from typing import Union, Dict, Optional

from aiohttp import web

from .. import types
from ..bot import api
from ..bot.base import Integer, String, Boolean, Float
from ..utils import json
from ..utils.payload import prepare_arg

DEFAULT_WEB_PATH = '/webhook'
BOT_DISPATCHER_KEY = 'BOT_DISPATCHER'


class WebhookRequestHandler(web.View):
    """
    Simple Wehhook request handler for aiohttp web server.

    You need to register that in app:

    .. code-block:: python3

        app.router.add_route('*', '/your/webhook/path', WebhookRequestHadler, name='webhook_handler')

    But first you need to configure application for getting Dispatcher instance from request handler!
    It must always be with key 'BOT_DISPATCHER'

    .. code-block:: python3

        bot = Bot(TOKEN, loop)
        dp = Dispatcher(bot)
        app['BOT_DISPATCHER'] = dp

    """

    def get_dispatcher(self):
        """
        Get Dispatcher instance from environment

        :return: :class:`aiogram.Dispatcher`
        """
        return self.request.app[BOT_DISPATCHER_KEY]

    async def parse_update(self, bot):
        """
        Read update from stream and deserialize it.

        :param bot: bot instance. You an get it from Dispatcher
        :return: :class:`aiogram.types.Update`
        """
        data = await self.request.json()
        update = types.Update.deserialize(data)
        bot.prepare_object(update, parent=bot)
        return update

    async def post(self):
        """
        Process POST request

        if one of handler returns instance of :class:`aiogram.dispatcher.webhook.BaseResponse` return it to webhook.
        Otherwise do nothing (return 'ok')

        :return: :class:`aiohttp.web.Response`
        """
        dispatcher = self.get_dispatcher()
        update = await self.parse_update(dispatcher.bot)
        results = await dispatcher.process_update(update)

        for result in results:
            if isinstance(result, BaseResponse):
                return result.get_web_response()
        return web.Response(text='ok')


def configure_app(dispatcher, app: web.Application, path=DEFAULT_WEB_PATH):
    """
    You can prepare web.Application for working with webhook handler.

    :param dispatcher: Dispatcher instance
    :param app: :class:`aiohttp.web.Application`
    :param path: Path to your webhook.
    :return:
    """
    app.router.add_route('*', path, WebhookRequestHandler, name='webhook_handler')
    app[BOT_DISPATCHER_KEY] = dispatcher


def get_new_configured_app(dispatcher, path=DEFAULT_WEB_PATH):
    """
    Create new :class:`aiohttp.web.Application` and configure it.

    :param dispatcher: Dispatcher instance
    :param path: Path to your webhook.
    :return:
    """
    app = web.Application()
    configure_app(dispatcher, app, path)
    return app


class BaseResponse:
    """
    Base class for webhook responses.
    """
    method = None

    def prepare(self) -> typing.Dict:
        """
        You need to override this method.

        :return: response parameters dict
        """
        raise NotImplementedError

    def cleanup(self) -> typing.Dict:
        """
        Cleanup response after preparing. Remove empty fields.

        :return: response parameters dict
        """
        return {k: v for k, v in self.prepare().items() if v is not None}

    def get_response(self):
        """
        Get response object

        :return:
        """
        return {'method': self.method, **self.cleanup()}

    def get_web_response(self):
        """
        Get prepared web response with JSON data.

        :return: :class:`aiohttp.web.Response`
        """
        return web.json_response(self.get_response(), dumps=json.dumps)

    async def execute_response(self, bot):
        """
        Use this method if you want to execute response as simple HTTP request.

        :param bot: Bot instance.
        :return:
        """
        return await bot.request(self.method, self.cleanup())


class SendMessage(BaseResponse):
    """
    You can send message with webhook by using this instance of this object.
    All arguments is equal with :method:`Bot.send_message` method.
    """
    __slots__ = ('chat_id', 'text', 'parse_mode',
                 'disable_web_page_preview', 'disable_notification',
                 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_MESSAGE

    def __init__(self, chat_id: Union[Integer, String],
                 text: String,
                 parse_mode: Optional[String] = None,
                 disable_web_page_preview: Optional[Boolean] = None,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[Union[
                     types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
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
        """
        self.chat_id = chat_id
        self.text = text
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self) -> dict:
        return {
            'chat_id': self.chat_id,
            'text': self.text,
            'parse_mode': self.parse_mode,
            'disable_web_page_preview': self.disable_web_page_preview,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup)
        }


class ForwardMessage(BaseResponse):
    """
    Forward message from
    """
    __slots__ = ('chat_id', 'from_chat_id', 'message_id', 'disable_notification')

    method = api.Methods.FORWARD_MESSAGE

    def __init__(self, chat_id: Union[Integer, String],
                 from_chat_id: Union[Integer, String],
                 message_id: Integer,
                 disable_notification: Optional[Boolean] = None):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of the
            target channel (in the format @channelusername)
        :param from_chat_id: Union[Integer, String] - Unique identifier for the chat where the original
            message was sent (or channel username in the format @channelusername)
        :param disable_notification: Boolean (Optional) - Sends the message silently. Users will receive a
            notification with no sound.
        :param message_id: Integer - Message identifier in the chat specified in from_chat_id
        """
        self.chat_id = chat_id
        self.from_chat_id = from_chat_id
        self.message_id = message_id
        self.disable_notification = disable_notification

    def prepare(self) -> dict:
        return {
            'chat_id': self.chat_id,
            'from_chat_id': self.from_chat_id,
            'message_id': self.message_id,
            'disable_notification': self.disable_notification
        }


class SendPhoto(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'photo', 'caption', 'disable_notification', 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_PHOTO

    def __init__(self, chat_id: Union[Integer, String],
                 photo: String,
                 caption: Optional[String] = None,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[Union[
                     types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of
            the target channel (in the format @channelusername)
        :param photo: String - Photo to send. Pass a file_id as String to send
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
        """
        self.chat_id = chat_id
        self.photo = photo
        self.caption = caption
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'photo': self.photo,
            'caption': self.caption,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup)
        }


class SendAudio(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'audio', 'caption', 'duration', 'performer', 'title',
                 'disable_notification', 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_AUDIO

    def __init__(self, chat_id: Union[Integer, String],
                 audio: String,
                 caption: Optional[String] = None,
                 duration: Optional[Integer] = None,
                 performer: Optional[String] = None,
                 title: Optional[String] = None,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[Union[
                     types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param audio: String - Audio file to send. Pass a file_id as String
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
        """
        self.chat_id = chat_id
        self.audio = audio
        self.caption = caption
        self.duration = duration
        self.performer = performer
        self.title = title
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'audio': self.audio,
            'caption': self.caption,
            'duration': self.duration,
            'performer': self.performer,
            'title': self.title,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup)
        }


class SendDocument(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'document', 'caption', 'disable_notification', 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_DOCUMENT

    def __init__(self, chat_id: Union[Integer, String],
                 document: String,
                 caption: Optional[String] = None,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[Union[
                     types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param document: String - File to send. Pass a file_id as String
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
        """
        self.chat_id = chat_id
        self.document = document
        self.caption = caption
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'document': self.document,
            'caption': self.caption,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup),
        }


class SendVideo(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'video', 'duration', 'width', 'height', 'caption', 'disable_notification',
                 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_VIDEO

    def __init__(self, chat_id: Union[Integer, String],
                 video: String,
                 duration: Optional[Integer] = None,
                 width: Optional[Integer] = None,
                 height: Optional[Integer] = None,
                 caption: Optional[String] = None,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[Union[
                     types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param video: String - Video to send. Pass a file_id as String
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
        """
        self.chat_id = chat_id
        self.video = video
        self.duration = duration
        self.width = width
        self.height = height
        self.caption = caption
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'video': self.video,
            'duration': self.duration,
            'width': self.width,
            'height': self.height,
            'caption': self.caption,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup)
        }


class SendVoice(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'voice', 'caption', 'duration', 'disable_notification',
                 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_VOICE

    def __init__(self, chat_id: Union[Integer, String],
                 voice: String,
                 caption: Optional[String] = None,
                 duration: Optional[Integer] = None,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[Union[
                     types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param voice: String - Audio file to send. Pass a file_id as String
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
        """
        self.chat_id = chat_id
        self.voice = voice
        self.caption = caption
        self.duration = duration
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'voice': self.voice,
            'caption': self.caption,
            'duration': self.duration,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup)
        }


class SendVideoNote(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'video_note', 'duration', 'length', 'disable_notification',
                 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_VIDEO_NOTE

    def __init__(self, chat_id: Union[Integer, String],
                 video_note: String,
                 duration: Optional[Integer] = None,
                 length: Optional[Integer] = None,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[Union[
                     types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
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
        """
        self.chat_id = chat_id
        self.video_note = video_note
        self.duration = duration
        self.length = length
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'video_note': self.video_note,
            'duration': self.duration,
            'length': self.length,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup)
        }


class SendLocation(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'latitude', 'longitude', 'disable_notification', 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_LOCATION

    def __init__(self, chat_id: Union[Integer, String],
                 latitude: Float, longitude: Float,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[Union[
                     types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
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
        """
        self.chat_id = chat_id
        self.latitude = latitude
        self.longitude = longitude
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup)
        }


class SendVenue(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'latitude', 'longitude', 'title', 'address', 'foursquare_id',
                 'disable_notification', 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_VENUE

    def __init__(self, chat_id: Union[Integer, String],
                 latitude: Float,
                 longitude: Float,
                 title: String,
                 address: String,
                 foursquare_id: Optional[String] = None,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[Union[
                     types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
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
        """
        self.chat_id = chat_id
        self.latitude = latitude
        self.longitude = longitude
        self.title = title
        self.address = address
        self.foursquare_id = foursquare_id
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'title': self.title,
            'address': self.address,
            'foursquare_id': self.foursquare_id,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup)
        }


class SendContact(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'phone_number', 'first_name', 'last_name', 'disable_notification',
                 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_CONTACT

    def __init__(self, chat_id: Union[Integer, String],
                 phone_number: String,
                 first_name: String,
                 last_name: Optional[String] = None,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[Union[
                     types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
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
        """
        self.chat_id = chat_id
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'phone_number': self.phone_number,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup)
        }


class SendChatAction(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'action')

    method = api.Methods.SEND_CHAT_ACTION

    def __init__(self, chat_id: Union[Integer, String], action: String):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param action: String - Type of action to broadcast. Choose one, depending on what the user is about to receive:
            typing for text messages, upload_photo for photos, record_video or upload_video for videos,
            record_audio or upload_audio for audio files, upload_document for general files,
            find_location for location data, record_video_note or upload_video_note for video notes.
        """
        self.chat_id = chat_id
        self.action = action

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'action': self.action
        }


class KickChatMember(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'user_id', 'until_date')

    method = api.Methods.KICK_CHAT_MEMBER

    def __init__(self, chat_id: Union[Integer, String],
                 user_id: Integer,
                 until_date: Optional[
                     Union[Integer, datetime.datetime, datetime.timedelta]] = None):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target group or username
            of the target supergroup or channel (in the format @channelusername)
        :param user_id: Integer - Unique identifier of the target user
        :param until_date: Integer - Date when the user will be unbanned, unix time. If user is banned for
            more than 366 days or less than 30 seconds from the current time they are considered to be banned forever
        """
        self.chat_id = chat_id
        self.user_id = user_id
        self.until_date = until_date

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'until_date': prepare_arg(self.until_date)
        }


class UnbanChatMember(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'user_id')

    method = api.Methods.UNBAN_CHAT_MEMBER

    def __init__(self, chat_id: Union[Integer, String], user_id: Integer):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target group or
            username of the target supergroup or channel (in the format @username)
        :param user_id: Integer - Unique identifier of the target user
        """
        self.chat_id = chat_id
        self.user_id = user_id

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'user_id': self.user_id
        }


class Empty(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'user_id', 'until_date', 'can_send_messages', 'can_send_media_messages',
                 'can_send_other_messages', 'can_add_web_page_previews')

    method = api.Methods.RESTRICT_CHAT_MEMBER

    def __init__(self, chat_id: Union[Integer, String],
                 user_id: Integer,
                 until_date: Optional[Union[Integer, datetime.datetime, datetime.timedelta]] = None,
                 can_send_messages: Optional[Boolean] = None,
                 can_send_media_messages: Optional[Boolean] = None,
                 can_send_other_messages: Optional[Boolean] = None,
                 can_add_web_page_previews: Optional[Boolean] = None):
        """
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
        """
        self.chat_id = chat_id
        self.user_id = user_id
        self.until_date = until_date
        self.can_send_messages = can_send_messages
        self.can_send_media_messages = can_send_media_messages
        self.can_send_other_messages = can_send_other_messages
        self.can_add_web_page_previews = can_add_web_page_previews

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'until_date': prepare_arg(self.until_date),
            'can_send_messages': self.can_send_messages,
            'can_send_media_messages': self.can_send_media_messages,
            'can_send_other_messages': self.can_send_other_messages,
            'can_add_web_page_previews': self.can_add_web_page_previews
        }


class PromoteChatMember(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'user_id', 'can_change_info', 'can_post_messages', 'can_edit_messages',
                 'can_delete_messages', 'can_invite_users', 'can_restrict_members', 'can_pin_messages',
                 'can_promote_members')

    method = api.Methods.PROMOTE_CHAT_MEMBER

    def __init__(self, chat_id: Union[Integer, String],
                 user_id: Integer,
                 can_change_info: Optional[Boolean] = None,
                 can_post_messages: Optional[Boolean] = None,
                 can_edit_messages: Optional[Boolean] = None,
                 can_delete_messages: Optional[Boolean] = None,
                 can_invite_users: Optional[Boolean] = None,
                 can_restrict_members: Optional[Boolean] = None,
                 can_pin_messages: Optional[Boolean] = None,
                 can_promote_members: Optional[Boolean] = None):
        """
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
        """
        self.chat_id = chat_id
        self.user_id = user_id
        self.can_change_info = can_change_info
        self.can_post_messages = can_post_messages
        self.can_edit_messages = can_edit_messages
        self.can_delete_messages = can_delete_messages
        self.can_invite_users = can_invite_users
        self.can_restrict_members = can_restrict_members
        self.can_pin_messages = can_pin_messages
        self.can_promote_members = can_promote_members

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'can_change_info': self.can_change_info,
            'can_post_messages': self.can_post_messages,
            'can_edit_messages': self.can_edit_messages,
            'can_delete_messages': self.can_delete_messages,
            'can_invite_users': self.can_invite_users,
            'can_restrict_members': self.can_restrict_members,
            'can_pin_messages': self.can_pin_messages,
            'can_promote_members': self.can_promote_members
        }


class DeleteChatPhoto(BaseResponse):
    """

    """
    __slots__ = ('chat_id',)

    method = api.Methods.DELETE_CHAT_PHOTO

    def __init__(self, chat_id: Union[Integer, String]):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat
            or username of the target channel (in the format @channelusername)
        """
        self.chat_id = chat_id

    def prepare(self):
        return {
            'chat_id': self.chat_id
        }


class SetChatTitle(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'title')

    method = api.Methods.SET_CHAT_TITLE

    def __init__(self, chat_id: Union[Integer, String], title: String):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param title: String - New chat title, 1-255 characters
        """
        self.chat_id = chat_id
        self.title = title

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'title': self.title
        }


class SetChatDescription(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'description')

    method = api.Methods.SET_CHAT_DESCRIPTION

    def __init__(self, chat_id: Union[Integer, String], description: String):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat
            or username of the target channel (in the format @channelusername)
        :param description: String - New chat description, 0-255 characters
        """
        self.chat_id = chat_id
        self.description = description

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'description': self.description
        }


class PinChatMessage(BaseResponse):
    """

    """
    __slots__ = ('chat_id', 'message_id', 'disable_notification')

    method = api.Methods.PIN_CHAT_MESSAGE

    def __init__(self, chat_id: Union[Integer, String], message_id: Integer,
                 disable_notification: Optional[Boolean] = None):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat
            or username of the target supergroup (in the format @supergroupusername)
        :param message_id: Integer - Identifier of a message to pin
        :param disable_notification: Boolean - Pass True, if it is not necessary to send a notification
            to all group members about the new pinned message
        """
        self.chat_id = chat_id
        self.message_id = message_id
        self.disable_notification = disable_notification

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'disable_notification': self.disable_notification,
        }


class UnpinChatMessage(BaseResponse):
    """

    """
    __slots__ = ('chat_id',)

    method = api.Methods.UNPIN_CHAT_MESSAGE

    def __init__(self, chat_id: Union[Integer, String]):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or
            username of the target supergroup (in the format @supergroupusername)
        """
        self.chat_id = chat_id

    def prepare(self):
        return {
            'chat_id': self.chat_id
        }


class LeaveChat(BaseResponse):
    """

    """
    __slots__ = ('chat_id',)

    method = api.Methods.LEAVE_CHAT

    def __init__(self, chat_id: Union[Integer, String]):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat
            or username of the target supergroup or channel (in the format @channelusername)
        """
        self.chat_id = chat_id

    def prepare(self):
        return {
            'chat_id': self.chat_id
        }


class AnswerCallbackQuery(BaseResponse):
    """

    """
    __slots__ = ('callback_query_id', 'text', 'show_alert', 'url', 'cache_time')

    method = api.Methods.ANSWER_CALLBACK_QUERY

    def __init__(self, callback_query_id: String,
                 text: Optional[String] = None,
                 show_alert: Optional[Boolean] = None,
                 url: Optional[String] = None,
                 cache_time: Optional[Integer] = None):
        """
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
        """
        self.callback_query_id = callback_query_id
        self.text = text
        self.show_alert = show_alert
        self.url = url
        self.cache_time = cache_time

    def prepare(self):
        return {
            'callback_query_id': self.callback_query_id,
            'text': self.text,
            'show_alert': self.show_alert,
            'url': self.url,
            'cache_time': self.cache_time
        }


class Empty(BaseResponse):
    """

    """
    __slots__ = ()

    method = api.Methods

    def __init__(self):
        """

        """
        pass

    def prepare(self):
        return {}
