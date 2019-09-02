import os
import pathlib


class Downloadable:
    """
    Mixin for files
    """

    async def download(self, destination=None, timeout=30, chunk_size=65536, seek=True, make_dirs=True):
        """
        Download file

        :param destination: filename or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO`
        :param timeout: Integer
        :param chunk_size: Integer
        :param seek: Boolean - go to start of file when downloading is finished.
        :param make_dirs: Make dirs if not exist
        :return: destination
        """
        file = await self.get_file()

        is_path = True
        if destination is None:
            destination = file.file_path
        elif isinstance(destination, (str, pathlib.Path)) and os.path.isdir(destination):
            destination = os.path.join(destination, file.file_path)
        else:
            is_path = False

        if is_path and make_dirs:
            os.makedirs(os.path.dirname(destination), exist_ok=True)

        return await self.bot.download_file(file_path=file.file_path, destination=destination, timeout=timeout,
                                            chunk_size=chunk_size, seek=seek)

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
