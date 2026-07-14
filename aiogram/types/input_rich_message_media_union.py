from typing import TypeAlias

from .input_media_animation import InputMediaAnimation
from .input_media_audio import InputMediaAudio
from .input_media_photo import InputMediaPhoto
from .input_media_video import InputMediaVideo
from .input_media_voice_note import InputMediaVoiceNote

InputRichMessageMediaUnion: TypeAlias = (
    InputMediaAnimation | InputMediaAudio | InputMediaPhoto | InputMediaVideo | InputMediaVoiceNote
)
