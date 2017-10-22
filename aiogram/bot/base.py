import asyncio
import io
from typing import Dict, List, Optional, Union

import aiohttp

from . import api
from ..types import base
from ..utils import json


class BaseBot:
    """
    Base class for bot. It's raw bot.
    """

    def __init__(self, token: base.String,
                 loop: Optional[Union[asyncio.BaseEventLoop, asyncio.AbstractEventLoop]] = None,
                 connections_limit: Optional[base.Integer] = 10,
                 proxy: str = None, proxy_auth: Optional[aiohttp.BasicAuth] = None,
                 continue_retry: Optional[bool] = False,
                 validate_token: Optional[bool] = True):
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
        :param continue_retry: automatic retry sent request when flood control exceeded
        :type continue_retry: :obj:`bool`
        :param validate_token: Validate token.
        :type validate_token: :obj:`bool`
        :raise: when token is invalid throw an :obj:`aiogram.utils.exceptions.ValidationError`
        """
        # Authentication
        if validate_token:
            api.check_token(token)
        self.__token = token

        # Proxy settings
        self.proxy = proxy
        self.proxy_auth = proxy_auth

        # Action on error
        self.continue_retry = continue_retry

        # Asyncio loop instance
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop

        # aiohttp main session
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=connections_limit),
            loop=self.loop, json_serialize=json.dumps)

        # Temp sessions
        self._temp_sessions = []

        # Data stored in bot instance
        self._data = {}

    def __del__(self):
        """
        When bot object is deleting - need close all sessions
        """
        for session in self._temp_sessions:
            if not session.closed:
                session.close()
        if self.session and not self.session.closed:
            self.session.close()

    def create_temp_session(self, limit: int = 1) -> aiohttp.ClientSession:
        """
        Create temporary session

        :param limit: Limit of connections
        :type limit: :obj:`int`
        :return: New session
        :rtype: :obj:`aiohttp.TCPConnector`
        """
        session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=limit, force_close=True),
            loop=self.loop, json_serialize=json.dumps)
        self._temp_sessions.append(session)
        return session

    def destroy_temp_session(self, session: aiohttp.ClientSession):
        """
        Destroy temporary session

        :param session: target session
        :type session: :obj:`aiohttp.ClientSession`
        """
        if not session.closed:
            session.close()
        if session in self._temp_sessions:
            self._temp_sessions.remove(session)

    async def request(self, method: base.String,
                      data: Optional[Dict] = None,
                      files: Optional[Dict] = None) -> Union[List, Dict, base.Boolean]:
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
        return await api.request(self.session, self.__token, method, data, files,
                                 proxy=self.proxy, proxy_auth=self.proxy_auth,
                                 continue_retry=self.continue_retry)

    async def download_file(self, file_path: base.String,
                            destination: Optional[base.InputFile] = None,
                            timeout: Optional[base.Integer] = 30,
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

        session = self.create_temp_session()
        url = api.Methods.file_url(token=self.__token, path=file_path)

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
    def data(self) -> Dict:
        """
        Data stored in bot object

        :return: Dictionary
        """
        return self._data

    def __setitem__(self, key, value):
        """
        Store data in bot instance

        :param key: Key in dict
        :param value: Value
        """
        self._data[key] = value

    def __getitem__(self, item):
        """
        Get item from bot instance by key

        :param item: key name
        :return: value
        """
        return self._data[item]

    def get(self, key, default=None):
        """
        Get item from bot instance by key or return default value

        :param key: key in dict
        :param default: default value
        :return: value or default value
        """
        return self._data.get(key, default)
