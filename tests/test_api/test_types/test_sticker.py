from aiogram.enums import StickerType
from aiogram.types import Sticker


class TestSticker:
    def test_get_profile_photos(self):
        sticker = Sticker(
            file_id="test",
            file_unique_id="test",
            type=StickerType.REGULAR,
            width=100,
            height=100,
            is_animated=False,
            is_video=False,
        )

        method = sticker.set_position_in_set(position=1)
        assert method.sticker == sticker.file_id

    def test_delete_from_set(self):
        sticker = Sticker(
            file_id="test",
            file_unique_id="test",
            type=StickerType.REGULAR,
            width=100,
            height=100,
            is_animated=False,
            is_video=False,
        )

        method = sticker.delete_from_set()
        assert method.sticker == sticker.file_id
