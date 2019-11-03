from __future__ import annotations

from .base import TelegramObject


class InputFile(TelegramObject):
    """
    This object represents the contents of a file to be uploaded. Must be posted using multipart/form-data in the usual way that files are uploaded via the browser.

    Source: https://core.telegram.org/bots/api#inputfile
    """
