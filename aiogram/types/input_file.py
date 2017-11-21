import io
import logging
import os
import tempfile
import time

import aiohttp

from . import base
from ..bot import api

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
        else:
            # As io.BytesIO
            assert isinstance(path_or_bytesio, io.IOBase)
            self._path = None
            self._file = path_or_bytesio

        self._filename = filename

    def __del__(self):
        """
        Close file descriptor
        """
        if not hasattr(self, '_file'):
            return
        self._file.close()
        del self._file

        if self.conf.get('downloaded') and self.conf.get('temp'):
            log.debug(f"Unlink file '{self._path}'")
            os.unlink(self._path)

    def get_filename(self) -> str:
        """
        Get file name

        :return: name
        """
        if self._filename is None:
            self._filename = api._guess_filename(self._file)
        return self._filename

    def get_file(self):
        """
        Get file object

        :return:
        """
        return self._file

    @classmethod
    async def from_url(cls, url, filename=None, temp_file=False, chunk_size=65536):
        """
        Download file from URL

        Manually is not required action. You can send urls instead!

        :param url: target URL
        :param filename: optional. set custom file name
        :param temp_file: use temporary file
        :param chunk_size:

        :return: InputFile
        """
        conf = {
            'downloaded': True,
            'url': url
        }

        # Let's do magic with the filename
        if filename:
            filename_prefix, _, ext = filename.rpartition('.')
            file_suffix = '.' + ext if ext else ''
        else:
            filename_prefix, _, ext = url.rpartition('/')[-1].rpartition('.')
            file_suffix = '.' + ext if ext else ''
            filename = filename_prefix + file_suffix

        async with aiohttp.ClientSession() as session:
            start = time.time()
            async with session.get(url) as response:
                if temp_file:
                    # Create temp file
                    fd, path = tempfile.mkstemp(suffix=file_suffix, prefix=filename_prefix + '_')
                    file = conf['temp'] = path

                    # Save file in temp directory
                    with open(fd, 'wb') as f:
                        await cls._process_stream(response, f, chunk_size=chunk_size)
                else:
                    # Save file in memory
                    file = await cls._process_stream(response, io.BytesIO(), chunk_size=chunk_size)

                log.debug(f"File successful downloaded at {round(time.time() - start, 2)} seconds from '{url}'")
                return cls(file, filename, conf=conf)

    @classmethod
    async def _process_stream(cls, response, writer, chunk_size=65536):
        """
        Transfer data

        :param response:
        :param writer:
        :param chunk_size:
        :return:
        """
        while True:
            chunk = await response.content.read(chunk_size)
            if not chunk:
                break
            writer.write(chunk)

        if writer.seekable():
            writer.seek(0)

        return writer

    def to_python(self):
        raise TypeError('Object of this type is not exportable!')

    @classmethod
    def to_object(cls, data):
        raise TypeError('Object of this type is not importable!')
