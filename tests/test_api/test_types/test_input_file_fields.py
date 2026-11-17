import pytest

from aiogram.types import (
    BufferedInputFile,
    InputMediaLivePhoto,
    InputMediaSticker,
    InputMediaVoiceNote,
    InputPaidMediaLivePhoto,
    InputStoryContentPhoto,
    InputStoryContentVideo,
    TelegramObject,
)

FILE = BufferedInputFile(b"data", filename="file")


@pytest.mark.parametrize(
    "type_,fields",
    [
        [InputStoryContentPhoto, ["photo"]],
        [InputStoryContentVideo, ["video"]],
        [InputMediaLivePhoto, ["media", "photo"]],
        [InputPaidMediaLivePhoto, ["media", "photo"]],
        [InputMediaSticker, ["media"]],
        [InputMediaVoiceNote, ["media"]],
    ],
)
def test_accepts_uploaded_file(type_: type[TelegramObject], fields: list[str]):
    # These fields take `attach://<name>`, so they must accept an `InputFile` upload.
    obj = type_(**dict.fromkeys(fields, FILE))
    for field in fields:
        assert getattr(obj, field) is FILE
