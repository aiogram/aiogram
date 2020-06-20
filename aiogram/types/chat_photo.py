import os
import pathlib

from . import base
from . import fields


class ChatPhoto(base.TelegramObject):
    """
    This object represents a chat photo.

    https://core.telegram.org/bots/api#chatphoto
    """
    small_file_id: base.String = fields.Field()
    small_file_unique_id: base.String = fields.Field()
    big_file_id: base.String = fields.Field()
    big_file_unique_id: base.String = fields.Field()

    async def download_small(self, destination=None, timeout=30, chunk_size=65536, seek=True, make_dirs=True):
        """
        Download file

        :param destination: filename or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO`
        :param timeout: Integer
        :param chunk_size: Integer
        :param seek: Boolean - go to start of file when downloading is finished.
        :param make_dirs: Make dirs if not exist
        :return: destination
        """
        file = await self.get_small_file()

        is_path = True
        if destination is None:
            destination = file.file_path
        elif isinstance(destination, (str, pathlib.Path)) and os.path.isdir(destination):
            os.path.join(destination, file.file_path)
        else:
            is_path = False

        if is_path and make_dirs:
            os.makedirs(os.path.dirname(destination), exist_ok=True)

        return await self.bot.download_file(file_path=file.file_path, destination=destination, timeout=timeout,
                                            chunk_size=chunk_size, seek=seek)

    async def download_big(self, destination=None, timeout=30, chunk_size=65536, seek=True, make_dirs=True):
        """
        Download file

        :param destination: filename or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO`
        :param timeout: Integer
        :param chunk_size: Integer
        :param seek: Boolean - go to start of file when downloading is finished.
        :param make_dirs: Make dirs if not exist
        :return: destination
        """
        file = await self.get_big_file()

        is_path = True
        if destination is None:
            destination = file.file_path
        elif isinstance(destination, (str, pathlib.Path)) and os.path.isdir(destination):
            os.path.join(destination, file.file_path)
        else:
            is_path = False

        if is_path and make_dirs:
            os.makedirs(os.path.dirname(destination), exist_ok=True)

        return await self.bot.download_file(file_path=file.file_path, destination=destination, timeout=timeout,
                                            chunk_size=chunk_size, seek=seek)

    async def get_small_file(self):
        return await self.bot.get_file(self.small_file_id)

    async def get_big_file(self):
        return await self.bot.get_file(self.big_file_id)

    def __hash__(self):
        return hash(self.small_file_id) + hash(self.big_file_id)
