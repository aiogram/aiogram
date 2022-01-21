import asyncio
import contextlib
import io
import os
import pathlib
import ssl
import typing
import warnings
from contextvars import ContextVar
from typing import Dict, List, Optional, Union, Type

import aiohttp
import certifi
from aiohttp.helpers import sentinel

from . import api
from .api import TelegramAPIServer, TELEGRAM_PRODUCTION
from ..types import ParseMode, base
from ..utils import json
from ..utils.auth_widget import check_integrity
from ..utils.deprecated import deprecated


class BaseBot:
    """
    Base class for bot. It's raw bot.
    """
    _ctx_timeout = ContextVar('TelegramRequestTimeout')
    _ctx_token = ContextVar('BotDifferentToken')

    def __init__(
            self,
            token: base.String,
            loop: Optional[Union[asyncio.BaseEventLoop, asyncio.AbstractEventLoop]] = None,
            connections_limit: Optional[base.Integer] = None,
            proxy: Optional[base.String] = None,
            proxy_auth: Optional[aiohttp.BasicAuth] = None,
            validate_token: Optional[base.Boolean] = True,
            parse_mode: typing.Optional[base.String] = None,
            disable_web_page_preview: Optional[base.Boolean] = None,
            timeout: typing.Optional[typing.Union[base.Integer, base.Float, aiohttp.ClientTimeout]] = None,
            server: TelegramAPIServer = TELEGRAM_PRODUCTION
    ):
        """
        Instructions how to get Bot token is found here: https://core.telegram.org/bots#3-how-do-i-create-a-bot

        :param token: token from @BotFather
        :type token: :obj:`str`
        :param loop: event loop
        :type loop: Optional Union :obj:`asyncio.BaseEventLoop`, :obj:`asyncio.AbstractEventLoop`
        :param connections_limit: connections limit for aiohttp.ClientSession
        :type connections_limit: :obj:`int`
        :param proxy: HTTP proxy URL
        :type proxy: :obj:`str`
        :param proxy_auth: Authentication information
        :type proxy_auth: Optional :obj:`aiohttp.BasicAuth`
        :param validate_token: Validate token.
        :type validate_token: :obj:`bool`
        :param parse_mode: You can set default parse mode
        :type parse_mode: :obj:`str`
        :param disable_web_page_preview: You can set default disable web page preview parameter
        :type disable_web_page_preview: :obj:`bool`
        :param timeout: Request timeout
        :type timeout: :obj:`typing.Optional[typing.Union[base.Integer, base.Float, aiohttp.ClientTimeout]]`
        :param server: Telegram Bot API Server endpoint.
        :type server: :obj:`TelegramAPIServer`
        :raise: when token is invalid throw an :obj:`aiogram.utils.exceptions.ValidationError`
        """
        self._main_loop = loop

        # Authentication
        if validate_token:
            api.check_token(token)
        self._token = None
        self.__token = token
        self.id = int(token.split(sep=':')[0])
        self.server = server

        self.proxy = proxy
        self.proxy_auth = proxy_auth

        # aiohttp main session
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        self._session: Optional[aiohttp.ClientSession] = None
        self._connector_class: Type[aiohttp.TCPConnector] = aiohttp.TCPConnector
        self._connector_init = dict(limit=connections_limit, ssl=ssl_context)

        if isinstance(proxy, str) and (proxy.startswith('socks5://') or proxy.startswith('socks4://')):
            from aiohttp_socks import SocksConnector
            from aiohttp_socks.utils import parse_proxy_url

            socks_ver, host, port, username, password = parse_proxy_url(proxy)
            if proxy_auth:
                if not username:
                    username = proxy_auth.login
                if not password:
                    password = proxy_auth.password

            self._connector_class = SocksConnector
            self._connector_init.update(
                socks_ver=socks_ver, host=host, port=port,
                username=username, password=password, rdns=True,
            )
            self.proxy = None
            self.proxy_auth = None

        self._timeout = None
        self.timeout = timeout

        self.parse_mode = parse_mode

        self.disable_web_page_preview = disable_web_page_preview

    async def get_new_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            connector=self._connector_class(**self._connector_init),
            json_serialize=json.dumps
        )

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self._main_loop

    async def get_session(self) -> Optional[aiohttp.ClientSession]:
        if self._session is None or self._session.closed:
            self._session = await self.get_new_session()

        if not self._session._loop.is_running():  # NOQA
            # Hate `aiohttp` devs because it juggles event-loops and breaks already opened session
            # So... when we detect a broken session need to fix it by re-creating it
            # @asvetlov, if you read this, please no more juggle event-loop inside aiohttp, it breaks the brain.
            await self._session.close()
            self._session = await self.get_new_session()

        return self._session

    @property
    @deprecated(
        reason="Client session should be created inside async function, use `await bot.get_session()` instead",
        stacklevel=3,
    )
    def session(self) -> Optional[aiohttp.ClientSession]:
        return self._session

    @staticmethod
    def _prepare_timeout(
            value: typing.Optional[typing.Union[base.Integer, base.Float, aiohttp.ClientTimeout]]
    ) -> typing.Optional[aiohttp.ClientTimeout]:
        if value is None or isinstance(value, aiohttp.ClientTimeout):
            return value
        return aiohttp.ClientTimeout(total=value)

    @property
    def timeout(self):
        timeout = self._ctx_timeout.get(self._timeout)
        if timeout is None:
            return sentinel
        return timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = self._prepare_timeout(value)

    @timeout.deleter
    def timeout(self):
        self.timeout = None

    @contextlib.contextmanager
    def request_timeout(self, timeout: typing.Union[base.Integer, base.Float, aiohttp.ClientTimeout]):
        """
        Context manager implements opportunity to change request timeout in current context

        :param timeout: Request timeout
        :type timeout: :obj:`typing.Optional[typing.Union[base.Integer, base.Float, aiohttp.ClientTimeout]]`
        :return:
        """
        timeout = self._prepare_timeout(timeout)
        token = self._ctx_timeout.set(timeout)
        try:
            yield
        finally:
            self._ctx_timeout.reset(token)

    @property
    def __token(self):
        return self._ctx_token.get(self._token)

    @__token.setter
    def __token(self, value):
        self._token = value

    @contextlib.contextmanager
    def with_token(self, bot_token: base.String, validate_token: Optional[base.Boolean] = True):
        if validate_token:
            api.check_token(bot_token)
        token = self._ctx_token.set(bot_token)
        try:
            yield
        finally:
            self._ctx_token.reset(token)

    @deprecated("This method's behavior will be changed in aiogram v3.0. "
                "More info: https://core.telegram.org/bots/api#close", stacklevel=3)
    async def close(self):
        """
        Close all client sessions
        """
        if self._session:
            await self._session.close()

    async def request(self, method: base.String,
                      data: Optional[Dict] = None,
                      files: Optional[Dict] = None, **kwargs) -> Union[List, Dict, base.Boolean]:
        """
        Make an request to Telegram Bot API

        https://core.telegram.org/bots/api#making-requests

        :param method: API method
        :type method: :obj:`str`
        :param data: request parameters
        :type data: :obj:`dict`
        :param files: files
        :type files: :obj:`dict`
        :return: result
        :rtype: Union[List, Dict]
        :raise: :obj:`aiogram.exceptions.TelegramApiError`
        """

        return await api.make_request(await self.get_session(), self.server, self.__token, method, data, files,
                                      proxy=self.proxy, proxy_auth=self.proxy_auth, timeout=self.timeout, **kwargs)

    async def download_file(
            self,
            file_path: base.String,
            destination: Optional[Union[base.InputFile, pathlib.Path]] = None,
            timeout: Optional[base.Integer] = sentinel,
            chunk_size: Optional[base.Integer] = 65536,
            seek: Optional[base.Boolean] = True,
            destination_dir: Optional[Union[str, pathlib.Path]] = None,
            make_dirs: Optional[base.Boolean] = True,
    ) -> Union[io.BytesIO, io.FileIO]:
        """
        Download file by file_path to destination file or directory

        if You want to automatically create destination (:class:`io.BytesIO`) use default
        value of destination and handle result of this method.

        At most one of these parameters can be used: :param destination:, :param destination_dir:

        :param file_path: file path on telegram server (You can get it from :obj:`aiogram.types.File`)
        :type file_path: :obj:`str`
        :param destination: filename or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO`
        :param timeout: Integer
        :param chunk_size: Integer
        :param seek: Boolean - go to start of file when downloading is finished.
        :param destination_dir: directory for saving files
        :param make_dirs: Make dirs if not exist
        :return: destination
        """
        if destination and destination_dir:
            raise ValueError(
                "Use only one of the parameters:destination or destination_dir."
            )

        if destination is None and destination_dir is None:
            destination = io.BytesIO()

        elif destination_dir:
            destination = os.path.join(destination_dir, file_path)

        if make_dirs and not isinstance(destination, io.IOBase) and os.path.dirname(destination):
            os.makedirs(os.path.dirname(destination), exist_ok=True)

        url = self.get_file_url(file_path)

        dest = destination if isinstance(destination, io.IOBase) else open(destination, 'wb')
        session = await self.get_session()
        async with session.get(
            url,
            timeout=timeout,
            proxy=self.proxy,
            proxy_auth=self.proxy_auth,
            raise_for_status=True,
        ) as response:
            while True:
                chunk = await response.content.read(chunk_size)
                if not chunk:
                    break
                dest.write(chunk)
                dest.flush()
        if seek:
            dest.seek(0)
        return dest

    def get_file_url(self, file_path):
        return self.server.file_url(token=self.__token, path=file_path)

    async def send_file(self, file_type, method, file, payload) -> Union[Dict, base.Boolean]:
        """
        Send file

        https://core.telegram.org/bots/api#inputfile

        :param file_type: field name
        :param method: API method
        :param file: String or io.IOBase
        :param payload: request payload
        :return: response
        """
        if file is None:
            files = {}
        elif isinstance(file, str):
            # You can use file ID or URL in the most of requests
            payload[file_type] = file
            files = None
        else:
            files = {file_type: file}

        return await self.request(method, payload, files)

    @property
    def parse_mode(self):
        return getattr(self, '_parse_mode', None)

    @parse_mode.setter
    def parse_mode(self, value):
        if value is None:
            setattr(self, '_parse_mode', None)
        else:
            if not isinstance(value, str):
                raise TypeError(f"Parse mode must be str, not {type(value)}")
            value = value.lower()
            if value not in ParseMode.all():
                raise ValueError(f"Parse mode must be one of {ParseMode.all()}")
            setattr(self, '_parse_mode', value)
            if value == 'markdown':
                warnings.warn("Parse mode `Markdown` is legacy since Telegram Bot API 4.5, "
                              "retained for backward compatibility. Use `MarkdownV2` instead.\n"
                              "https://core.telegram.org/bots/api#markdown-style", stacklevel=3)

    @parse_mode.deleter
    def parse_mode(self):
        self.parse_mode = None

    @property
    def disable_web_page_preview(self):
        return getattr(self, '_disable_web_page_preview', None)

    @disable_web_page_preview.setter
    def disable_web_page_preview(self, value):
        if value is None:
            setattr(self, '_disable_web_page_preview', None)
        else:
            if not isinstance(value, bool):
                raise TypeError(f"Disable web page preview must be bool, not {type(value)}")
            setattr(self, '_disable_web_page_preview', value)

    @disable_web_page_preview.deleter
    def disable_web_page_preview(self):
        self.disable_web_page_preview = None

    def check_auth_widget(self, data):
        return check_integrity(self.__token, data)
