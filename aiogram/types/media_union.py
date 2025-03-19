from typing import Union

from .input_media_audio import InputMediaAudio
from .input_media_document import InputMediaDocument
from .input_media_photo import InputMediaPhoto
from .input_media_video import InputMediaVideo

MediaUnion = Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]
