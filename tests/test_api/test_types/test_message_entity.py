import pytest

from aiogram.types import MessageEntity
from tests.deprecated import check_deprecated


class TestMessageEntity:
    def test_extract(self):
        entity = MessageEntity(type="hashtag", length=4, offset=5)
        assert entity.extract("#foo #bar #baz") == "#bar"

    def test_get_text(self):
        entity = MessageEntity(type="hashtag", length=4, offset=5)
        with check_deprecated("3.2", exception=AttributeError):
            assert entity.get_text("#foo #bar #baz") == "#bar"
