from .base import Deserializable


class File(Deserializable):
    """
    This object represents a file ready to be downloaded.
    
    The file can be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>.
    
    It is guaranteed that the link will be valid for at least 1 hour. When the link expires, 
    a new one can be requested by calling getFile.
    
    https://core.telegram.org/bots/api#file
    """
    def __init__(self, file_id, file_size, file_path):
        self.file_id: str = file_id
        self.file_size: int = file_size
        self.file_path: str = file_path

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        file_id = raw_data.get('file_id')
        file_size = raw_data.get('file_size')
        file_path = raw_data.get('file_path')

        return File(file_id, file_size, file_path)

    async def download(self, destination=None, timeout=30, chunk_size=65536, seek=True):
        return await self.bot.download_file(self.file_path, destination, timeout, chunk_size, seek)
