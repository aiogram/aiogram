from aiogram.types import MessageEntity


class TestMessageEntity:
    def test_extract(self):
        entity = MessageEntity(type="hashtag", length=4, offset=5)
        assert entity.extract("#foo #bar #baz") == "#bar"
