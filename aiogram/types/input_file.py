import io
import logging
import os

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
        elif isinstance(path_or_bytesio, io.IOBase):
            self._path = None
            self._file = path_or_bytesio
        else:
            raise TypeError('Not supported file type.')

        self._filename = filename

    def __del__(self):
        """
        Close file descriptor
        """
        self._file.close()

    @property
    def filename(self):
        if self._filename is None:
            self._filename = api._guess_filename(self._file)
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

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

    def to_python(self):
        raise TypeError('Object of this type is not exportable!')

    @classmethod
    def to_object(cls, data):
        raise TypeError('Object of this type is not importable!')
