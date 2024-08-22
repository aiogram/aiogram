import pytest
from pydantic import ValidationError

from aiogram.client.default import DefaultBotProperties
from aiogram.default_annotations import DefaultLinkPreviewOptions, DefaultParseMode
from aiogram.enums import ParseMode
from aiogram.types import LinkPreviewOptions, TelegramObject
from tests.mocked_bot import MockedBot


class TestDefault:
    def test_default_validation(self):
        class TestObject(TelegramObject):
            parse_mode: DefaultParseMode = None

        obj1 = TestObject()
        assert obj1.parse_mode is None
        obj2 = TestObject(parse_mode=ParseMode.HTML)
        assert obj2.parse_mode == ParseMode.HTML
        obj3 = TestObject(parse_mode="HTML")
        assert obj3.parse_mode == ParseMode.HTML
        with pytest.raises(ValidationError):
            TestObject(parse_mode=b"some invalid type")

    def test_remain_value_after_dump_roundtrip(self):
        bot = MockedBot(default=DefaultBotProperties())

    def test_link_preview_options_defined(self):
        class TestObject(TelegramObject):
            options: DefaultLinkPreviewOptions = None

        # won't raise error
        TestObject(options=LinkPreviewOptions())


class TestDefaultBotProperties:
    def test_is_empty(self):
        default_bot_properties = DefaultBotProperties()
        assert default_bot_properties.is_empty

        default_bot_properties = DefaultBotProperties(protect_content=True)
        assert not default_bot_properties.is_empty
