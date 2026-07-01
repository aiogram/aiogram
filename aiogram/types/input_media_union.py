from __future__ import annotations

from typing import Annotated, TypeAlias

from pydantic import Field

from .input_media_animation import InputMediaAnimation
from .input_media_audio import InputMediaAudio
from .input_media_document import InputMediaDocument
from .input_media_live_photo import InputMediaLivePhoto
from .input_media_photo import InputMediaPhoto
from .input_media_video import InputMediaVideo

InputMediaUnion: TypeAlias = Annotated[
    InputMediaAnimation
    | InputMediaAudio
    | InputMediaDocument
    | InputMediaLivePhoto
    | InputMediaPhoto
    | InputMediaVideo,
    Field(discriminator="type"),
]
