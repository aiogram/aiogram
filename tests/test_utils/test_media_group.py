import pytest

from aiogram.types import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    MessageEntity,
)
from aiogram.utils.media_group import MediaGroupBuilder


class TestMediaGroupBuilder:
    def test_add_incorrect_media(self):
        builder = MediaGroupBuilder()
        with pytest.raises(ValueError):
            builder._add("test")

    def test_add_more_than_10_media(self):
        builder = MediaGroupBuilder()
        for _ in range(10):
            builder.add_photo("test")
        with pytest.raises(ValueError):
            builder.add_photo("test")

    def test_extend(self):
        builder = MediaGroupBuilder()
        media = InputMediaPhoto(media="test")

        builder._extend([media, media])
        assert len(builder._media) == 2

    def test_add_audio(self):
        builder = MediaGroupBuilder()
        builder.add_audio("test")
        assert isinstance(builder._media[0], InputMediaAudio)

    def test_add_photo(self):
        builder = MediaGroupBuilder()
        builder.add_photo("test")
        assert isinstance(builder._media[0], InputMediaPhoto)

    def test_add_video(self):
        builder = MediaGroupBuilder()
        builder.add_video("test")
        assert isinstance(builder._media[0], InputMediaVideo)

    def test_add_document(self):
        builder = MediaGroupBuilder()
        builder.add_document("test")
        assert isinstance(builder._media[0], InputMediaDocument)

    @pytest.mark.parametrize(
        "type,result_type",
        [
            ("audio", InputMediaAudio),
            ("photo", InputMediaPhoto),
            ("video", InputMediaVideo),
            ("document", InputMediaDocument),
        ],
    )
    def test_add(self, type, result_type):
        builder = MediaGroupBuilder()
        builder.add(type=type, media="test")
        assert isinstance(builder._media[0], result_type)

    def test_add_unknown_type(self):
        builder = MediaGroupBuilder()
        with pytest.raises(ValueError):
            builder.add(type="unknown", media="test")

    def test_build(self):
        builder = MediaGroupBuilder()
        builder.add_photo("test")
        assert builder.build() == builder._media

    def test_build_empty(self):
        builder = MediaGroupBuilder()
        assert builder.build() == []

    def test_build_with_caption(self):
        builder = MediaGroupBuilder(
            caption="override caption",
            caption_entities=[MessageEntity(type="bold", offset=0, length=8)],
        )
        builder.add_photo("test", caption="test")
        builder.add_photo("test", caption="test")
        builder.add_photo("test", caption="test")

        media = builder.build()
        assert len(media) == 3
        assert media[0].caption == "override caption"
        assert media[1].caption == "test"
        assert media[2].caption == "test"
