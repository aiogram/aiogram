import asyncio
import inspect
import io
import logging
import os
import secrets

import aiohttp

from . import base
from ..bot import api

CHUNK_SIZE = 65536

log = logging.getLogger('aiogram')


class InputFile(base.TelegramObject):
    """
    This object represents the contents of a file to be uploaded.
    Must be posted using multipart/form-data in the usual way that files are uploaded via the browser.

    Also that is not typical TelegramObject!

    https://core.telegram.org/bots/api#inputfile
    """

    def __init__(self, path_or_bytesio, filename=None, conf=None):
        """

        :param path_or_bytesio:
        :param filename:
        :param conf:
        """
        super(InputFile, self).__init__(conf=conf)
        if isinstance(path_or_bytesio, str):
            # As path
            self._file = open(path_or_bytesio, 'rb')
            self._path = path_or_bytesio
            if filename is None:
                filename = os.path.split(path_or_bytesio)[-1]
        elif isinstance(path_or_bytesio, io.IOBase):
            self._path = None
            self._file = path_or_bytesio
        elif isinstance(path_or_bytesio, _WebPipe):
            self._path = None
            self._file = path_or_bytesio
        else:
            raise TypeError('Not supported file type.')

        self._filename = filename

        self.attachment_key = secrets.token_urlsafe(16)

    def __del__(self):
        """
        Close file descriptor
        """
        if not hasattr(self, '_file'):
            return

        if inspect.iscoroutinefunction(self._file.close):
            return asyncio.ensure_future(self._file.close())
        self._file.close()

    @property
    def filename(self):
        if self._filename is None:
            self._filename = api.guess_filename(self._file)
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def attach(self):
        return f"attach://{self.attachment_key}"

    def get_filename(self) -> str:
        """
        Get file name

        :return: name
        """
        return self.filename

    @property
    def file(self):
        return self._file

    def get_file(self):
        """
        Get file object

        :return:
        """
        return self.file

    @classmethod
    def from_url(cls, url, filename=None, chunk_size=CHUNK_SIZE):
        """
        Download file from URL

        Manually is not required action. You can send urls instead!

        :param url: target URL
        :param filename: optional. set custom file name
        :param chunk_size:

        :return: InputFile
        """
        pipe = _WebPipe(url, chunk_size=chunk_size)
        if filename is None:
            filename = pipe.name

        return cls(pipe, filename, chunk_size)

    def save(self, filename, chunk_size=CHUNK_SIZE):
        """
        Write file to disk

        :param filename:
        :param chunk_size:
        """
        with open(filename, 'wb') as fp:
            while True:
                # Chunk writer
                data = self.file.read(chunk_size)
                if not data:
                    break
                fp.write(data)
            # Flush all data
            fp.flush()

        # Go to start of file.
        if self.file.seekable():
            self.file.seek(0)

    def __str__(self):
        return f"<InputFile 'attach://{self.attachment_key}' with file='{self.file}'>"

    __repr__ = __str__

    def to_python(self):
        raise TypeError('Object of this type is not exportable!')

    @classmethod
    def to_object(cls, data):
        raise TypeError('Object of this type is not importable!')


class _WebPipe:
    def __init__(self, url, chunk_size=-1):
        self.url = url
        self.chunk_size = chunk_size

        self._session: aiohttp.ClientSession = None
        self._response: aiohttp.ClientResponse = None
        self._reader = None
        self._name = None

        self._lock = asyncio.Lock()

    @property
    def name(self):
        if not self._name:
            *_, part = self.url.rpartition('/')
            if part:
                self._name = part
            else:
                self._name = secrets.token_urlsafe(24)
        return self._name

    async def open(self):
        session = self._session = aiohttp.ClientSession()
        self._response = await session.get(self.url)  # type: aiohttp.ClientResponse
        await self._lock.acquire()

        return self

    async def close(self):
        if self._response and not self._response.closed:
            await self._response.close()
        if self._session and not self._session.closed:
            await self._session.close()
        if self._lock.locked():
            self._lock.release()

    @property
    def closed(self):
        return not self._session or self._session.closed

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.closed:
            await self.open()

        chunk = await self.read(self.chunk_size)
        if not chunk:
            await self.close()
            raise StopAsyncIteration
        return chunk

    async def read(self, chunk_size=-1):
        if not self._response:
            raise LookupError('I/O operation on closed stream')
        response: aiohttp.ClientResponse = self._response
        reader: aiohttp.StreamReader = response.content

        return await reader.read(chunk_size)

    def __str__(self):
        result = f"WebPipe url='{self.url}', name='{self.name}'"
        return '<' + result + '>'

    __repr__ = __str__
