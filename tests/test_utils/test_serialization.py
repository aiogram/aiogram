from datetime import datetime

import pytest
from pydantic_core import PydanticSerializationError

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatType, MessageEntityType, ParseMode
from aiogram.methods import SendMessage
from aiogram.types import Chat, LinkPreviewOptions, Message, MessageEntity, User
from aiogram.utils.serialization import (
    DeserializedTelegramObject,
    deserialize_telegram_object,
    deserialize_telegram_object_to_python,
)


class TestSerialize:
    def test_deserialize(self):
        method = SendMessage(chat_id=42, text="<b>test</b>", parse_mode="HTML")
        deserialized = deserialize_telegram_object(method)
        assert isinstance(deserialized, DeserializedTelegramObject)
        assert isinstance(deserialized.data, dict)
        assert deserialized.data["chat_id"] == 42

    def test_deserialize_default(self):
        message = Message(
            message_id=42,
            date=datetime.now(),
            chat=Chat(id=42, type=ChatType.PRIVATE, first_name="Test"),
            from_user=User(id=42, first_name="Test", is_bot=False),
            text="https://example.com",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            entities=[MessageEntity(type=MessageEntityType.URL, length=19, offset=0)],
        )
        with pytest.raises(PydanticSerializationError):
            # https://github.com/aiogram/aiogram/issues/1450
            message.model_dump_json(exclude_none=True)

        deserialized = deserialize_telegram_object(message)
        assert deserialized.data["link_preview_options"] == {"is_disabled": True}
        assert isinstance(deserialized.data["date"], int)

    def test_deserialize_with_custom_default(self):
        default = DefaultBotProperties(parse_mode="HTML")
        method = SendMessage(chat_id=42, text="<b>test</b>")

        deserialized = deserialize_telegram_object(method, default=default)
        assert deserialized.data["parse_mode"] == ParseMode.HTML
        assert deserialized.data["parse_mode"] != method.parse_mode

    def test_deserialize_telegram_object_to_python(self):
        method = SendMessage(chat_id=42, text="<b>test</b>", parse_mode="HTML")
        deserialized = deserialize_telegram_object_to_python(method)
        assert isinstance(deserialized, dict)
