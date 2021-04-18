import asyncio
import asyncio.tasks
import datetime
import functools
import ipaddress
import itertools
import typing
import logging
from typing import Dict, List, Optional, Union

from aiohttp import web
from aiohttp.web_exceptions import HTTPGone

from .. import types
from ..bot import api
from ..types import ParseMode
from ..types.base import Boolean, Float, Integer, String
from ..utils import helper, markdown
from ..utils import json
from ..utils.deprecated import warn_deprecated as warn
from ..utils.exceptions import TimeoutWarning
from ..utils.payload import prepare_arg

DEFAULT_WEB_PATH = '/webhook'
DEFAULT_ROUTE_NAME = 'webhook_handler'
BOT_DISPATCHER_KEY = 'BOT_DISPATCHER'

RESPONSE_TIMEOUT = 55

WEBHOOK = 'webhook'
WEBHOOK_CONNECTION = 'WEBHOOK_CONNECTION'
WEBHOOK_REQUEST = 'WEBHOOK_REQUEST'

TELEGRAM_SUBNET_1 = ipaddress.IPv4Network('149.154.160.0/20')
TELEGRAM_SUBNET_2 = ipaddress.IPv4Network('91.108.4.0/22')

allowed_ips = set()

log = logging.getLogger(__name__)


def _check_ip(ip: str) -> bool:
    """
    Check IP in range

    :param ip:
    :return:
    """
    address = ipaddress.IPv4Address(ip)
    return address in allowed_ips


def allow_ip(*ips: typing.Union[str, ipaddress.IPv4Network, ipaddress.IPv4Address]):
    """
    Allow ip address.

    :param ips:
    :return:
    """
    for ip in ips:
        if isinstance(ip, ipaddress.IPv4Address):
            allowed_ips.add(ip)
        elif isinstance(ip, str):
            allowed_ips.add(ipaddress.IPv4Address(ip))
        elif isinstance(ip, ipaddress.IPv4Network):
            allowed_ips.update(ip.hosts())
        else:
            raise ValueError(f"Bad type of ipaddress: {type(ip)} ('{ip}')")


# Allow access from Telegram servers
allow_ip(TELEGRAM_SUBNET_1, TELEGRAM_SUBNET_2)


class WebhookRequestHandler(web.View):
    """
    Simple Wehhook request handler for aiohttp web server.

    You need to register that in app:

    .. code-block:: python3

        app.router.add_route('*', '/your/webhook/path', WebhookRequestHandler, name='webhook_handler')

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
        dp = self.request.app[BOT_DISPATCHER_KEY]
        try:
            from aiogram import Bot, Dispatcher
            Dispatcher.set_current(dp)
            Bot.set_current(dp.bot)
        except RuntimeError:
            pass
        return dp

    async def parse_update(self, bot):
        """
        Read update from stream and deserialize it.

        :param bot: bot instance. You an get it from Dispatcher
        :return: :class:`aiogram.types.Update`
        """
        data = await self.request.json()
        return types.Update(**data)

    async def post(self):
        """
        Process POST request

        if one of handler returns instance of :class:`aiogram.dispatcher.webhook.BaseResponse` return it to webhook.
        Otherwise do nothing (return 'ok')

        :return: :class:`aiohttp.web.Response`
        """
        self.validate_ip()

        # context.update_state({'CALLER': WEBHOOK,
        #                       WEBHOOK_CONNECTION: True,
        #                       WEBHOOK_REQUEST: self.request})

        dispatcher = self.get_dispatcher()
        update = await self.parse_update(dispatcher.bot)

        results = await self.process_update(update)
        response = self.get_response(results)

        if response:
            web_response = response.get_web_response()
        else:
            web_response = web.Response(text='ok')

        if self.request.app.get('RETRY_AFTER', None):
            web_response.headers['Retry-After'] = self.request.app['RETRY_AFTER']

        return web_response

    async def get(self):
        self.validate_ip()
        return web.Response(text='')

    async def head(self):
        self.validate_ip()
        return web.Response(text='')

    async def process_update(self, update):
        """
        Need respond in less than 60 seconds in to webhook.

        So... If you respond greater than 55 seconds webhook automatically respond 'ok'
        and execute callback response via simple HTTP request.

        :param update:
        :return:
        """
        dispatcher = self.get_dispatcher()
        loop = dispatcher.loop or asyncio.get_event_loop()

        # Analog of `asyncio.wait_for` but without cancelling task
        waiter = loop.create_future()
        timeout_handle = loop.call_later(RESPONSE_TIMEOUT, asyncio.tasks._release_waiter, waiter)
        cb = functools.partial(asyncio.tasks._release_waiter, waiter)

        fut = asyncio.ensure_future(dispatcher.updates_handler.notify(update), loop=loop)
        fut.add_done_callback(cb)

        try:
            try:
                await waiter
            except asyncio.CancelledError:
                fut.remove_done_callback(cb)
                fut.cancel()
                raise

            if fut.done():
                return fut.result()
            else:
                # context.set_value(WEBHOOK_CONNECTION, False)
                fut.remove_done_callback(cb)
                fut.add_done_callback(self.respond_via_request)
        finally:
            timeout_handle.cancel()

    def respond_via_request(self, task):
        """
        Handle response after 55 second.

        :param task:
        :return:
        """
        warn(f"Detected slow response into webhook. "
             f"(Greater than {RESPONSE_TIMEOUT} seconds)\n"
             f"Recommended to use 'async_task' decorator from Dispatcher for handler with long timeouts.",
             TimeoutWarning)

        dispatcher = self.get_dispatcher()
        loop = dispatcher.loop or asyncio.get_event_loop()

        try:
            results = task.result()
        except Exception as e:
            loop.create_task(
                dispatcher.errors_handlers.notify(dispatcher, types.Update.get_current(), e))
        else:
            response = self.get_response(results)
            if response is not None:
                asyncio.ensure_future(response.execute_response(dispatcher.bot), loop=loop)

    def get_response(self, results):
        """
        Get response object from results.

        :param results: list
        :return:
        """
        if results is None:
            return None
        for result in itertools.chain.from_iterable(results):
            if isinstance(result, BaseResponse):
                return result

    def check_ip(self):
        """
        Check client IP. Accept requests only from telegram servers.

        :return:
        """
        # For reverse proxy (nginx)
        forwarded_for = self.request.headers.get('X-Forwarded-For', None)
        if forwarded_for:
            return forwarded_for, _check_ip(forwarded_for)

        # For default method
        peer_name = self.request.transport.get_extra_info('peername')
        if peer_name is not None:
            host, _ = peer_name
            return host, _check_ip(host)

        # Not allowed and can't get client IP
        return None, False

    def validate_ip(self):
        """
        Check ip if that is needed. Raise web.HTTPUnauthorized for not allowed hosts.
        """
        if self.request.app.get('_check_ip', False):
            ip_address, accept = self.check_ip()
            if not accept:
                log.warning(f"Blocking request from an unauthorized IP: {ip_address}")
                raise web.HTTPUnauthorized()

            # context.set_value('TELEGRAM_IP', ip_address)


class GoneRequestHandler(web.View):
    """
    If a webhook returns the HTTP error 410 Gone for all requests for more than 23 hours successively,
    it can be automatically removed.
    """

    async def get(self):
        raise HTTPGone()

    async def post(self):
        raise HTTPGone()


def configure_app(dispatcher, app: web.Application, path=DEFAULT_WEB_PATH, route_name=DEFAULT_ROUTE_NAME):
    """
    You can prepare web.Application for working with webhook handler.

    :param dispatcher: Dispatcher instance
    :param app: :class:`aiohttp.web.Application`
    :param path: Path to your webhook.
    :param route_name: Name of webhook handler route
    :return:
    """
    app.router.add_route('*', path, WebhookRequestHandler, name=route_name)
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

    @property
    def method(self) -> str:
        """
        In all subclasses of that class you need to override this property

        :return: str
        """
        raise NotImplementedError

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
        method_name = helper.HelperMode.apply(self.method, helper.HelperMode.snake_case)
        method = getattr(bot, method_name, None)
        if method:
            return await method(**self.cleanup())
        return await bot.request(self.method, self.cleanup())

    async def __call__(self, bot=None):
        if bot is None:
            from aiogram import Bot
            bot = Bot.get_current()
        return await self.execute_response(bot)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self()


class ReplyToMixin:
    """
    Mixin for responses where from which can reply to messages.
    """

    def reply(self, message: typing.Union[int, types.Message]):
        """
        Reply to message

        :param message: :obj:`int` or  :obj:`types.Message`
        :return: self
        """
        setattr(self, 'reply_to_message_id', message.message_id if isinstance(message, types.Message) else message)
        return self

    def to(self, target: typing.Union[types.Message, types.Chat, types.base.Integer, types.base.String]):
        """
        Send to chat

        :param target: message or chat or id
        :return:
        """
        if isinstance(target, types.Message):
            chat_id = target.chat.id
        elif isinstance(target, types.Chat):
            chat_id = target.id
        elif isinstance(target, (int, str)):
            chat_id = target
        else:
            raise TypeError(f"Bad type of target. ({type(target)})")

        setattr(self, 'chat_id', chat_id)
        return self


class DisableNotificationMixin:
    def without_notification(self):
        """
        Disable notification

        :return:
        """
        setattr(self, 'disable_notification', True)
        return self


class DisableWebPagePreviewMixin:
    def no_web_page_preview(self):
        """
        Disable web page preview

        :return:
        """
        setattr(self, 'disable_web_page_preview', True)
        return self


class ParseModeMixin:
    def as_html(self):
        """
        Set parse_mode to HTML

        :return:
        """
        setattr(self, 'parse_mode', ParseMode.HTML)
        return self

    def as_markdown(self):
        """
        Set parse_mode to Markdown

        :return:
        """
        setattr(self, 'parse_mode', ParseMode.MARKDOWN)
        return self

    @staticmethod
    def _global_parse_mode():
        """
        Detect global parse mode

        :return:
        """
        from aiogram import Bot
        bot = Bot.get_current()
        if bot is not None:
            return bot.parse_mode


class SendMessage(BaseResponse, ReplyToMixin, ParseModeMixin, DisableNotificationMixin, DisableWebPagePreviewMixin):
    """
    You can send message with webhook by using this instance of this object.
    All arguments is equal with Bot.send_message method.
    """

    __slots__ = ('chat_id', 'text', 'parse_mode',
                 'disable_web_page_preview', 'disable_notification',
                 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_MESSAGE

    def __init__(self, chat_id: Union[Integer, String] = None,
                 text: String = None,
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
        if text is None:
            text = ''
        if parse_mode is None:
            parse_mode = self._global_parse_mode()

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
            'reply_markup': prepare_arg(self.reply_markup),
        }

    def write(self, *text, sep=' '):
        """
        Write text to response

        :param text:
        :param sep:
        :return:
        """
        self.text += markdown.text(*text, sep)
        return self

    def write_ln(self, *text, sep=' '):
        """
        Write line

        :param text:
        :param sep:
        :return:
        """
        if self.text and self.text[-1] != '\n':
            self.text += '\n'
        self.text += markdown.text(*text, sep) + '\n'
        return self


class ForwardMessage(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for forward messages of any kind on to webhook.
    """
    __slots__ = ('chat_id', 'from_chat_id', 'message_id', 'disable_notification')

    method = api.Methods.FORWARD_MESSAGE

    def __init__(self, chat_id: Union[Integer, String] = None,
                 from_chat_id: Union[Integer, String] = None,
                 message_id: Integer = None,
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

    def message(self, message: types.Message):
        """
        Select target message

        :param message:
        :return:
        """
        setattr(self, 'from_chat_id', message.chat.id)
        setattr(self, 'message_id', message.message_id)
        return self

    def prepare(self) -> dict:
        return {
            'chat_id': self.chat_id,
            'from_chat_id': self.from_chat_id,
            'message_id': self.message_id,
            'disable_notification': self.disable_notification
        }


class SendPhoto(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send photo on to webhook.
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
            0-1024 characters after entities parsing
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
            'reply_markup': prepare_arg(self.reply_markup),
        }


class SendAudio(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send audio on to webhook.
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
        :param caption: String (Optional) - Audio caption, 0-1024 characters after entities parsing
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
            'reply_markup': prepare_arg(self.reply_markup),
        }


class SendDocument(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send document on to webhook.
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
            (may also be used when resending documents by file_id), 0-1024 characters after entities parsing
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


class SendVideo(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send video on to webhook.
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
            0-1024 characters after entities parsing
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
            'reply_markup': prepare_arg(self.reply_markup),
        }


class SendVoice(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send voice on to webhook.
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
        :param caption: String (Optional) - Voice message caption, 0-1024 characters after entities parsing
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
            'reply_markup': prepare_arg(self.reply_markup),
        }


class SendVideoNote(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send video note on to webhook.
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
        :param video_note: String - Video note to send. Pass a file_id
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
            'reply_markup': prepare_arg(self.reply_markup),
        }


class SendMediaGroup(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use this method to send a group of photos or videos as an album.
    """

    __slots__ = ('chat_id', 'media', 'disable_notification', 'reply_to_message_id')

    method = api.Methods.SEND_MEDIA_GROUP

    def __init__(self, chat_id: Union[Integer, String],
                 media: Union[types.MediaGroup, List] = None,
                 disable_notification: typing.Optional[Boolean] = None,
                 reply_to_message_id: typing.Optional[Integer] = None):
        """
        Use this method to send a group of photos or videos as an album.

        Source: https://core.telegram.org/bots/api#sendmediagroup

        :param chat_id:	Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`typing.Union[base.Integer, base.String]`
        :param media: A JSON-serialized array describing photos and videos to be sent
        :type media: :obj:`typing.Union[types.MediaGroup, typing.List]`
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`typing.Optional[base.Boolean]`
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`typing.Optional[base.Integer]`
        :return: On success, an array of the sent Messages is returned.
        :rtype: typing.List[types.Message]
        """
        if media is None:
            media = types.MediaGroup()
        elif isinstance(media, list):
            # Convert list to MediaGroup
            media = types.MediaGroup(media)

        self.chat_id = chat_id
        self.media = media
        self.disable_notifications = disable_notification
        self.reply_to_message_id = reply_to_message_id

    def prepare(self):
        files = dict(self.media.get_files())
        if files:
            raise TypeError('Allowed only file ID or URL\'s')

        media = prepare_arg(self.media)

        return {
            'chat_id': self.chat_id,
            'media': media,
            'disable_notifications': self.disable_notifications,
            'reply_to_message_id': self.reply_to_message_id
        }

    def attach_photo(self, photo: String, caption: String = None):
        """
        Attach photo

        :param photo:
        :param caption:
        :return: self
        """
        self.media.attach_photo(photo, caption)
        return self

    def attach_video(self, video: String, caption: String = None, width: Integer = None,
                     height: Integer = None, duration: Integer = None):
        """
        Attach video

        :param video:
        :param caption:
        :param width:
        :param height:
        :param duration:
        :return: self
        """
        self.media.attach_video(video, caption, width=width, height=height, duration=duration)
        return self


class SendLocation(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send location on to webhook.
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
            'reply_markup': prepare_arg(self.reply_markup),
        }


class SendVenue(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send venue on to webhook.
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
            'reply_markup': prepare_arg(self.reply_markup),
        }


class SendContact(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send contact on to webhook.
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
            'reply_markup': prepare_arg(self.reply_markup),
        }


class SendChatAction(BaseResponse):
    """
    Use that response type for send chat action on to webhook.
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
    Use that response type for kick chat member on to webhook.
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
            'until_date': prepare_arg(self.until_date),
        }


class UnbanChatMember(BaseResponse):
    """
    Use that response type for unban chat member on to webhook.
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


class RestrictChatMember(BaseResponse):
    """
    Use that response type for restrict chat member on to webhook.
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
    Use that response type for promote chat member on to webhook.
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
    Use that response type for delete chat photo on to webhook.
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
    Use that response type for set chat title on to webhook.
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
    Use that response type for set chat description on to webhook.
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


class PinChatMessage(BaseResponse, DisableNotificationMixin):
    """
    Use that response type for pin chat message on to webhook.
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
    Use that response type for unpin chat message on to webhook.
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
    Use that response type for leave chat on to webhook.
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
    Use that response type for answer callback query on to webhook.
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


class EditMessageText(BaseResponse, ParseModeMixin, DisableWebPagePreviewMixin):
    """
    Use that response type for edit message text on to webhook.
    """

    __slots__ = ('chat_id', 'message_id', 'inline_message_id', 'text', 'parse_mode',
                 'disable_web_page_preview', 'reply_markup')

    method = api.Methods.EDIT_MESSAGE_TEXT

    def __init__(self, text: String,
                 chat_id: Optional[Union[Integer, String]] = None,
                 message_id: Optional[Integer] = None,
                 inline_message_id: Optional[String] = None,
                 parse_mode: Optional[String] = None,
                 disable_web_page_preview: Optional[Boolean] = None,
                 reply_markup: Optional[types.InlineKeyboardMarkup] = None):
        """
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
        """
        if parse_mode is None:
            parse_mode = self._global_parse_mode()

        self.chat_id = chat_id
        self.message_id = message_id
        self.inline_message_id = inline_message_id
        self.text = text
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'inline_message_id': self.inline_message_id,
            'text': self.text,
            'parse_mode': self.parse_mode,
            'disable_web_page_preview': self.disable_web_page_preview,
            'reply_markup': prepare_arg(self.reply_markup),
        }


class EditMessageCaption(BaseResponse):
    """
    Use that response type for edit message caption on to webhook.
    """

    __slots__ = ('chat_id', 'message_id', 'inline_message_id', 'caption', 'reply_markup')

    method = api.Methods.EDIT_MESSAGE_CAPTION

    def __init__(self, chat_id: Optional[Union[Integer, String]] = None,
                 message_id: Optional[Integer] = None,
                 inline_message_id: Optional[String] = None,
                 caption: Optional[String] = None,
                 reply_markup: Optional[types.InlineKeyboardMarkup] = None):
        """
        :param chat_id: Union[Integer, String] (Optional) - Required if inline_message_id
            is not specified. Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param message_id: Integer (Optional) - Required if inline_message_id is not specified.
            Identifier of the sent message
        :param inline_message_id: String (Optional) - Required if chat_id and message_id are not specified.
            Identifier of the inline message
        :param caption: String (Optional) - New caption of the message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for an inline keyboard.
        """
        self.chat_id = chat_id
        self.message_id = message_id
        self.inline_message_id = inline_message_id
        self.caption = caption
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'inline_message_id': self.inline_message_id,
            'caption': self.caption,
            'reply_markup': prepare_arg(self.reply_markup),
        }


class EditMessageReplyMarkup(BaseResponse):
    """
    Use that response type for edit message reply markup on to webhook.
    """

    __slots__ = ('chat_id', 'message_id', 'inline_message_id', 'reply_markup')

    method = api.Methods.EDIT_MESSAGE_REPLY_MARKUP

    def __init__(self, chat_id: Optional[Union[Integer, String]] = None,
                 message_id: Optional[Integer] = None,
                 inline_message_id: Optional[String] = None,
                 reply_markup: Optional[types.InlineKeyboardMarkup] = None):
        """
        :param chat_id: Union[Integer, String] (Optional) - Required if inline_message_id is not specified.
            Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :param message_id: Integer (Optional) - Required if inline_message_id is not specified.
            Identifier of the sent message
        :param inline_message_id: String (Optional) - Required if chat_id and message_id are not specified.
            Identifier of the inline message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for an inline keyboard.
        """
        self.chat_id = chat_id
        self.message_id = message_id
        self.inline_message_id = inline_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'inline_message_id': self.inline_message_id,
            'reply_markup': prepare_arg(self.reply_markup),
        }


class DeleteMessage(BaseResponse):
    """
    Use that response type for delete message on to webhook.
    """

    __slots__ = ('chat_id', 'message_id')

    method = api.Methods.DELETE_MESSAGE

    def __init__(self, chat_id: Union[Integer, String], message_id: Integer):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param message_id: Integer - Identifier of the message to delete
        """
        self.chat_id = chat_id
        self.message_id = message_id

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'message_id': self.message_id
        }


class SendSticker(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send sticker on to webhook.
    """

    __slots__ = ('chat_id', 'sticker', 'disable_notification', 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_STICKER

    def __init__(self, chat_id: Union[Integer, String],
                 sticker: String,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[
                     Union[types.InlineKeyboardMarkup,
                           types.ReplyKeyboardMarkup, Dict, String]] = None):
        """
        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param sticker: String - Sticker to send. Pass a file_id
            as String to send a file that exists on the Telegram servers (recommended),
            pass an HTTP URL as a String for Telegram to get a .webp file from the Internet,
            or upload a new one using multipart/form-data. More info on Sending Files »
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional) -
            Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        """
        self.chat_id = chat_id
        self.sticker = sticker
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'sticker': self.sticker,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup),
        }


class CreateNewStickerSet(BaseResponse):
    """
    Use that response type for create new sticker set on to webhook.
    """

    __slots__ = ('user_id', 'name', 'title', 'png_sticker', 'emojis', 'contains_masks', 'mask_position')

    method = api.Methods.CREATE_NEW_STICKER_SET

    def __init__(self, user_id: Integer,
                 name: String, title: String,
                 png_sticker: String,
                 emojis: String,
                 contains_masks: Optional[Boolean] = None,
                 mask_position: Optional[types.MaskPosition] = None):
        """
        :param user_id: Integer - User identifier of created sticker set owner
        :param name: String - Short name of sticker set, to be used in t.me/addstickers/ URLs (e.g., animals).
            Can contain only english letters, digits and underscores. Must begin with a letter,
            can't contain consecutive underscores and must end in “_by_<bot username>”. <bot_username>
            is case insensitive. 1-64 characters.
        :param title: String - Sticker set title, 1-64 characters
        :param png_sticker: String - Png image with the sticker,
            must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width
            or height must be exactly 512px. Pass a file_id as a String to send a file that
            already exists on the Telegram servers, pass an HTTP URL
            as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        :param emojis: String - One or more emoji corresponding to the sticker
        :param contains_masks: Boolean (Optional) - Pass True, if a set of mask stickers should be created
        :param mask_position: types.MaskPosition (Optional) - Position where the mask should be placed on faces
        """
        self.user_id = user_id
        self.name = name
        self.title = title
        self.png_sticker = png_sticker
        self.emojis = emojis
        self.contains_masks = contains_masks
        self.mask_position = mask_position

    def prepare(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'title': self.title,
            'png_sticker': self.png_sticker,
            'emojis': self.emojis,
            'contains_masks': self.contains_masks,
            'mask_position': self.mask_position
        }


class AddStickerToSet(BaseResponse):
    """
    Use that response type for add sticker to set on to webhook.
    """

    __slots__ = ('user_id', 'name', 'png_sticker', 'emojis', 'mask_position')

    method = api.Methods.ADD_STICKER_TO_SET

    def __init__(self, user_id: Integer,
                 name: String,
                 png_sticker: String,
                 emojis: String,
                 mask_position: Optional[types.MaskPosition] = None):
        """
        :param user_id: Integer - User identifier of sticker set owner
        :param name: String - Sticker set name
        :param png_sticker: String - Png image with the sticker,
            must be up to 512 kilobytes in size, dimensions must not exceed 512px,
            and either width or height must be exactly 512px. Pass a file_id as a String
            to send a file that already exists on the Telegram servers, pass an HTTP URL
            as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        :param emojis: String - One or more emoji corresponding to the sticker
        :param mask_position: types.MaskPosition (Optional) - Position where the mask should be placed on faces
        """
        self.user_id = user_id
        self.name = name
        self.png_sticker = png_sticker
        self.emojis = emojis
        self.mask_position = mask_position

    def prepare(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'png_sticker': self.png_sticker,
            'emojis': self.emojis,
            'mask_position': prepare_arg(self.mask_position),
        }


class SetStickerPositionInSet(BaseResponse):
    """
    Use that response type for set sticker position in set on to webhook.
    """

    __slots__ = ('sticker', 'position')

    method = api.Methods.SET_STICKER_POSITION_IN_SET

    def __init__(self, sticker: String, position: Integer):
        """
        :param sticker: String - File identifier of the sticker
        :param position: Integer - New sticker position in the set, zero-based
        """
        self.sticker = sticker
        self.position = position

    def prepare(self):
        return {
            'sticker': self.sticker,
            'position': self.position
        }


class DeleteStickerFromSet(BaseResponse):
    """
    Use that response type for delete sticker from set on to webhook.
    """

    __slots__ = ('sticker',)

    method = api.Methods.DELETE_STICKER_FROM_SET

    def __init__(self, sticker: String):
        """
        :param sticker: String - File identifier of the sticker
        """
        self.sticker = sticker

    def prepare(self):
        return {
            'sticker': self.sticker
        }


class AnswerInlineQuery(BaseResponse):
    """
    Use that response type for answer inline query on to webhook.
    """

    __slots__ = ('inline_query_id', 'results', 'cache_time', 'is_personal', 'next_offset',
                 'switch_pm_text', 'switch_pm_parameter')

    method = api.Methods.ANSWER_INLINE_QUERY

    def __init__(self, inline_query_id: String,
                 results: [types.InlineQueryResult],
                 cache_time: Optional[Integer] = None,
                 is_personal: Optional[Boolean] = None,
                 next_offset: Optional[String] = None,
                 switch_pm_text: Optional[String] = None,
                 switch_pm_parameter: Optional[String] = None):
        """
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
        """
        self.inline_query_id = inline_query_id
        self.results = results
        self.cache_time = cache_time
        self.is_personal = is_personal
        self.next_offset = next_offset
        self.switch_pm_text = switch_pm_text
        self.switch_pm_parameter = switch_pm_parameter

    def prepare(self):
        return {
            'inline_query_id': self.inline_query_id,
            'results': prepare_arg(self.results),
            'cache_time': self.cache_time,
            'is_personal': self.is_personal,
            'next_offset': self.next_offset,
            'switch_pm_text': self.switch_pm_text,
            'switch_pm_parameter': self.switch_pm_parameter,
        }


class SendInvoice(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send invoice on to webhook.
    """

    __slots__ = ('chat_id', 'title', 'description', 'payload', 'provider_token', 'start_parameter',
                 'currency', 'prices', 'photo_url', 'photo_size', 'photo_width', 'photo_height',
                 'need_name', 'need_phone_number', 'need_email', 'need_shipping_address', 
                 'send_phone_number_to_provider', 'send_email_to_provider', 'is_flexible',
                 'disable_notification', 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_INVOICE

    def __init__(self, chat_id: Integer,
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
                 send_phone_number_to_provider: Optional[Boolean] = None,
                 send_email_to_provider: Optional[Boolean] = None,
                 is_flexible: Optional[Boolean] = None,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[types.InlineKeyboardMarkup] = None):
        """
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
        :param send_phone_number_to_provider: Boolean (Optional) - Pass True, if user's phone number should be sent
            to provider
        :param send_email_to_provider: Boolean (Optional) - Pass True, if user's email address should be sent 
            to provider
        :param is_flexible: Boolean (Optional) - Pass True, if the final price depends on the shipping method
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for an inline keyboard.
            If empty, one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button.
        """
        self.chat_id = chat_id
        self.title = title
        self.description = description
        self.payload = payload
        self.provider_token = provider_token
        self.start_parameter = start_parameter
        self.currency = currency
        self.prices = prices
        self.photo_url = photo_url
        self.photo_size = photo_size
        self.photo_width = photo_width
        self.photo_height = photo_height
        self.need_name = need_name
        self.need_phone_number = need_phone_number
        self.need_email = need_email
        self.need_shipping_address = need_shipping_address
        self.send_phone_number_to_provider = send_phone_number_to_provider
        self.send_email_to_provider = send_email_to_provider
        self.is_flexible = is_flexible
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'title': self.title,
            'description': self.description,
            'payload': self.payload,
            'provider_token': self.provider_token,
            'start_parameter': self.start_parameter,
            'currency': self.currency,
            'prices': prepare_arg(self.prices),
            'photo_url': self.photo_url,
            'photo_size': self.photo_size,
            'photo_width': self.photo_width,
            'photo_height': self.photo_height,
            'need_name': self.need_name,
            'need_phone_number': self.need_phone_number,
            'need_email': self.need_email,
            'need_shipping_address': self.need_shipping_address,
            'send_phone_number_to_provider': self.send_phone_number_to_provider,
            'send_email_to_provider': self.send_email_to_provider,
            'is_flexible': self.is_flexible,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup),
        }


class AnswerShippingQuery(BaseResponse):
    """
    Use that response type for answer shipping query on to webhook.
    """

    __slots__ = ('shipping_query_id', 'ok', 'shipping_options', 'error_message')

    method = api.Methods.ANSWER_SHIPPING_QUERY

    def __init__(self, shipping_query_id: String,
                 ok: Boolean,
                 shipping_options: Optional[typing.List[types.ShippingOption]] = None,
                 error_message: Optional[String] = None):
        """
        :param shipping_query_id: String - Unique identifier for the query to be answered
        :param ok: Boolean - Specify True if delivery to the specified address is possible and
            False if there are any problems (for example, if delivery to the specified address is not possible)
        :param shipping_options: [types.ShippingOption] (Optional) - Required if ok is True.
            A JSON-serialized array of available shipping options.
        :param error_message: String (Optional) - Required if ok is False.
            Error message in human readable form that explains why it is impossible to complete the order
            (e.g. "Sorry, delivery to your desired address is unavailable').
            Telegram will display this message to the user.
        """
        self.shipping_query_id = shipping_query_id
        self.ok = ok
        self.shipping_options = shipping_options
        self.error_message = error_message

    def prepare(self):
        return {
            'shipping_query_id': self.shipping_query_id,
            'ok': self.ok,
            'shipping_options': prepare_arg(self.shipping_options),
            'error_message': self.error_message
        }


class AnswerPreCheckoutQuery(BaseResponse):
    """
    Use that response type for answer pre checkout query on to webhook.
    """

    __slots__ = ('pre_checkout_query_id', 'ok', 'error_message')

    method = api.Methods.ANSWER_PRE_CHECKOUT_QUERY

    def __init__(self, pre_checkout_query_id: String,
                 ok: Boolean,
                 error_message: Optional[String] = None):
        """
        :param pre_checkout_query_id: String - Unique identifier for the query to be answered
        :param ok: Boolean - Specify True if everything is alright (goods are available, etc.)
            and the bot is ready to proceed with the order. Use False if there are any problems.
        :param error_message: String (Optional) - Required if ok is False.
            Error message in human readable form that explains the reason for failure to proceed with the checkout
            (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy
            filling out your payment details. Please choose a different color or garment!").
            Telegram will display this message to the user.
        """
        self.pre_checkout_query_id = pre_checkout_query_id
        self.ok = ok
        self.error_message = error_message

    def prepare(self):
        return {
            'pre_checkout_query_id': self.pre_checkout_query_id,
            'ok': self.ok,
            'error_message': self.error_message
        }


class SendGame(BaseResponse, ReplyToMixin, DisableNotificationMixin):
    """
    Use that response type for send game on to webhook.
    """

    __slots__ = ('chat_id', 'game_short_name', 'disable_notification', 'reply_to_message_id', 'reply_markup')

    method = api.Methods.SEND_GAME

    def __init__(self, chat_id: Integer,
                 game_short_name: String,
                 disable_notification: Optional[Boolean] = None,
                 reply_to_message_id: Optional[Integer] = None,
                 reply_markup: Optional[types.InlineKeyboardMarkup] = None):
        """
        :param chat_id: Integer - Unique identifier for the target chat
        :param game_short_name: String - Short name of the game, serves as the unique identifier for the game.
            Set up your games via Botfather.
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for an inline keyboard.
            If empty, one ‘Play game_title’ button will be shown. If not empty, the first button must launch the game.
        """
        self.chat_id = chat_id
        self.game_short_name = game_short_name
        self.disable_notification = disable_notification
        self.reply_to_message_id = reply_to_message_id
        self.reply_markup = reply_markup

    def prepare(self):
        return {
            'chat_id': self.chat_id,
            'game_short_name': self.game_short_name,
            'disable_notification': self.disable_notification,
            'reply_to_message_id': self.reply_to_message_id,
            'reply_markup': prepare_arg(self.reply_markup),
        }
