import os
import pathlib
from typing import BinaryIO, Optional, Union

from aiogram.api.types.file import File


class Downloadable:
    """
    Mixin for files
    """
    async def download(
        self,
        destination: Optional[Union[BinaryIO, pathlib.Path, str]] = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        seek: bool = True,
        make_dirs: bool = True,
    ) -> Optional[BinaryIO]:
        """
        Download file

        :param destination: Filename, file path or instance of :class:`io.IOBase`. For e.g. :class:`io.BytesIO`, defaults to None
        :type destination: Optional[Union[BinaryIO, pathlib.Path, str]]
        :param timeout: Total timeout in seconds, defaults to 30
        :type timeout: int
        :param chunk_size: File chunks size, defaults to 64 kb
        :type chunk_size: int
        :param seek: Go to start of file when downloading is finished. Used only for destination with :class:`typing.BinaryIO` type, defaults to True
        :type seek: bool
        :param make_dirs: make dirs if not exist
        :return: destination
        """
        from aiogram.api.client.bot import Bot

        file = await self.get_file()

        is_path = True
        if destination is None:
            destination = file.file_path
        elif isinstance(destination, (str, pathlib.Path)) and os.path.isdir(destination):
            # file from self.get_file() always have file_path
            destination = os.path.join(destination, file.file_path)  # type: ignore
        else:
            is_path = False

        if is_path and make_dirs:
            # destination cannot be None or BinaryIO due to the checks above
            os.makedirs(os.path.dirname(destination), exist_ok=True)  # type: ignore

        return await Bot.get_current(no_error=False).download_file(
            file_path=file.file_path,
            destination=destination,
            timeout=timeout,
            chunk_size=chunk_size,
            seek=seek,
        )

    async def get_file(self) -> File:
        """
        Get file information

        :return: :obj:`aiogram.types.File`
        """
        from aiogram.api.client.bot import Bot

        if hasattr(self, "file_path"):
            # only the File object can contain file_path
            return self  # type: ignore
        else:
            # mixin is only used in objects containing file_id.
            return await Bot.get_current(no_error=False).get_file(self.file_id)  # type: ignore

    async def get_url(self) -> str:
        """
        Get file url.
        Attention!!
        This method has security vulnerabilities for the reason that result
        contains bot's *access token* in open form. Use at your own risk!

        :return: url
        """
        from aiogram.api.client.bot import Bot

        file = await self.get_file()
        return Bot.get_current(no_error=False).get_file_url(file.file_path)

    def __hash__(self):
        return hash(self.file_id)  # type: ignore
