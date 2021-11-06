import os
import pathlib
from io import IOBase
from typing import Union, Optional

from aiogram.utils.deprecated import warn_deprecated


class Downloadable:
    """
    Mixin for files
    """

    async def download(
            self,
            destination=None,
            timeout=30,
            chunk_size=65536,
            seek=True,
            make_dirs=True,
            *,
            destination_dir: Optional[Union[str, pathlib.Path]] = None,
            destination_file: Optional[Union[str, pathlib.Path, IOBase]] = None
    ):
        """
        Download file

        At most one of these parameters can be used: :param destination_dir:, :param destination_file:

        :param destination: deprecated, use :param destination_dir: or :param destination_file: instead
        :param timeout: Integer
        :param chunk_size: Integer
        :param seek: Boolean - go to start of file when downloading is finished.
        :param make_dirs: Make dirs if not exist
        :param destination_dir: directory for saving files
        :param destination_file: path to the file or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO`
        :return: destination
        """
        if destination:
            warn_deprecated(
                "destination parameter is deprecated, please use destination_dir or destination_file."
            )
        if destination_dir and destination_file:
            raise ValueError(
                "Use only one of the parameters: destination_dir or destination_file."
            )

        file, destination = await self._prepare_destination(
            destination,
            destination_dir,
            destination_file,
        )

        return await self.bot.download_file(
            file_path=file.file_path,
            destination=destination,
            timeout=timeout,
            chunk_size=chunk_size,
            seek=seek,
            make_dirs=make_dirs
        )

    async def _prepare_destination(self, dest, destination_dir, destination_file):
        file = await self.get_file()

        if not(any((dest, destination_dir, destination_file))):
            destination = file.file_path

        elif dest:  # backward compatibility
            if isinstance(dest, IOBase):
                return file, dest
            if isinstance(dest, (str, pathlib.Path)) and os.path.isdir(dest):
                destination = os.path.join(dest, file.file_path)
            else:
                destination = dest

        elif destination_dir:
            if isinstance(destination_dir, (str, pathlib.Path)):
                destination = os.path.join(destination_dir, file.file_path)
            else:
                raise TypeError("destination_dir must be str or pathlib.Path")
        else:
            if isinstance(destination_file, IOBase):
                return file, destination_file
            elif isinstance(destination_file, (str, pathlib.Path)):
                destination = destination_file
            else:
                raise TypeError("destination_file must be str, pathlib.Path or io.IOBase type")

        return file, destination

    async def get_file(self):
        """
        Get file information

        :return: :obj:`aiogram.types.File`
        """
        if hasattr(self, 'file_path'):
            return self
        else:
            return await self.bot.get_file(self.file_id)

    async def get_url(self):
        """
        Get file url.

        Attention!!
        This method has security vulnerabilities for the reason that result
        contains bot's *access token* in open form. Use at your own risk!

        :return: url
        """
        file = await self.get_file()
        return self.bot.get_file_url(file.file_path)

    def __hash__(self):
        return hash(self.file_id)
