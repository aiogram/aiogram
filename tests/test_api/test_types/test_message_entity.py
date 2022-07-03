from aiogram.types import MessageEntity
from tests.deprecated import check_deprecated


class TestMessageEntity:
    def test_extract_from(self):
        entity = MessageEntity(type="hashtag", length=4, offset=5)
        assert entity.extract_from("#foo #bar #baz") == "#bar"

    def test_extract(self):
        entity = MessageEntity(type="hashtag", length=4, offset=5)
        with check_deprecated("3.0b5", exception=AttributeError):
            assert entity.extract("#foo #bar #baz") == "#bar"
