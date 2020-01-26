from __future__ import annotations

from .base import MutableTelegramObject


class InputMedia(MutableTelegramObject):
    """
    This object represents the content of a media message to be sent. It should be one of
     - InputMediaAnimation
     - InputMediaDocument
     - InputMediaAudio
     - InputMediaPhoto
     - InputMediaVideo

    Source: https://core.telegram.org/bots/api#inputmedia
    """
