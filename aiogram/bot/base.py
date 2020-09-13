import asyncio
import contextlib
import io
import ssl
import typing
import warnings
from contextvars import ContextVar
from typing import Dict, List, Optional, Union, Type

import aiohttp
import certifi
from aiohttp.helpers import sentinel

from . import api
from ..types import ParseMode, base
from ..utils import json
from ..utils.auth_widget import check_integrity


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
            timeout: typing.Optional[typing.Union[base.Integer, base.Float, aiohttp.ClientTimeout]] = None
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
        :param timeout: Request timeout
        :type timeout: :obj:`typing.Optional[typing.Union[base.Integer, base.Float, aiohttp.ClientTimeout]]`
        :raise: when token is invalid throw an :obj:`aiogram.utils.exceptions.ValidationError`
        """
        self._main_loop = loop

        # Authentication
        if validate_token:
            api.check_token(token)
        self._token = None
        self.__token = token
        self.id = int(token.split(sep=':')[0])

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

    def get_new_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            connector=self._connector_class(**self._connector_init, loop=self._main_loop),
            loop=self._main_loop,
            json_serialize=json.dumps
        )

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self._main_loop

    @property
    def session(self) -> Optional[aiohttp.ClientSession]:
        if self._session is None or self._session.closed:
            self._session = self.get_new_session()
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

    async def close(self):
        """
        Close all client sessions
        """
        await self.session.close()

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
        return await api.make_request(self.session, self.__token, method, data, files,
                                      proxy=self.proxy, proxy_auth=self.proxy_auth, timeout=self.timeout, **kwargs)

    async def download_file(self, file_path: base.String,
                            destination: Optional[base.InputFile] = None,
                            timeout: Optional[base.Integer] = sentinel,
                            chunk_size: Optional[base.Integer] = 65536,
                            seek: Optional[base.Boolean] = True) -> Union[io.BytesIO, io.FileIO]:
        """
        Download file by file_path to destination

        if You want to automatically create destination (:class:`io.BytesIO`) use default
        value of destination and handle result of this method.

        :param file_path: file path on telegram server (You can get it from :obj:`aiogram.types.File`)
        :type file_path: :obj:`str`
        :param destination: filename or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO`
        :param timeout: Integer
        :param chunk_size: Integer
        :param seek: Boolean - go to start of file when downloading is finished.
        :return: destination
        """
        if destination is None:
            destination = io.BytesIO()

        url = self.get_file_url(file_path)

        dest = destination if isinstance(destination, io.IOBase) else open(destination, 'wb')
        async with self.session.get(url, timeout=timeout, proxy=self.proxy, proxy_auth=self.proxy_auth) as response:
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
        return api.Methods.file_url(token=self.__token, path=file_path)

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

    def check_auth_widget(self, data):
        return check_integrity(self.__token, data)
