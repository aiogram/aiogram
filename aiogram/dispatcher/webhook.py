import typing
from typing import Union, Dict, Optional

from aiohttp import web

from aiogram import types
from aiogram.bot import api
from aiogram.bot.base import Integer, String, Boolean
from aiogram.utils.payload import prepare_arg
from ..utils import json

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
