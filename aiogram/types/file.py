from . import base
from . import fields


class File(base.TelegramObject):
    """
    This object represents a file ready to be downloaded.

    The file can be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>.

    It is guaranteed that the link will be valid for at least 1 hour.
    When the link expires, a new one can be requested by calling getFile.

    Maximum file size to download is 20 MB

    https://core.telegram.org/bots/api#file
    """
    file_id: base.String = fields.Field()
    file_size: base.Integer = fields.Field()
    file_path: base.String = fields.Field()

    async def download(self, destination=None, timeout=30, chunk_size=65536, seek=True):
        """
        Download file by file_path to destination

        :param destination: filename or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO`
        :param timeout: Integer
        :param chunk_size: Integer
        :param seek: Boolean - go to start of file when downloading is finished.
        :return: destination
        """
        return await self.bot.download_file(self.file_path, destination, timeout, chunk_size, seek)

    def __hash__(self):
        return self.file_id

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other.file_id == self.file_id
        return self.file_id == other
