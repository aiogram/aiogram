from . import base


# TODO: Interface for sending files


class InputFile(base.TelegramObject):
    """
    This object represents the contents of a file to be uploaded.
    Must be posted using multipart/form-data in the usual way that files are uploaded via the browser.

    https://core.telegram.org/bots/api#inputfile
    """

    def __init__(self, file_id=None, path=None, url=None, filename=None):
        self.file_id = file_id
        self.path = path
        self.url = url
        self.filename = filename
        super(InputFile, self).__init__()
