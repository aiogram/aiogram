from unittest.mock import sentinel

import pytest

from aiogram.client.default import Default
from aiogram.methods import GetMe, SendMessage, TelegramMethod
from aiogram.types import Chat, TelegramObject, User
from aiogram.types.base import UNSET
from tests.mocked_bot import MockedBot


class TestTelegramMethodRemoveUnset:
    @pytest.mark.parametrize(
        "values,names",
        [
            [{}, set()],
            [{"foo": "bar"}, {"foo"}],
            [{"foo": "bar", "baz": sentinel.DEFAULT}, {"foo"}],
        ],
    )
    @pytest.mark.parametrize("obj", [TelegramMethod, TelegramObject])
    def test_remove_unset(self, values, names, obj):
        validated = obj.remove_unset(values)
        assert set(validated.keys()) == names

    @pytest.mark.parametrize("obj", [TelegramMethod, TelegramObject])
    def test_remove_unset_non_dict(self, obj):
        assert obj.remove_unset("") == ""

    def test_method_strips_unset_on_validation(self):
        # UNSET can reach an outbound model through Bot.method_name, so
        # TelegramMethod must keep stripping it before field validation.
        method = SendMessage.model_validate({"chat_id": 42, "text": "test", "parse_mode": UNSET})

        # UNSET is dropped, so the field falls back to its declared default
        assert method.parse_mode == Default("parse_mode")

    def test_object_keeps_unset_out_of_the_validation_path(self):
        # Telegram never sends UNSET, so TelegramObject does not pay for a
        # before-validator on every inbound model. The helper still exists for
        # external callers, but it is not registered as a model validator.
        assert "remove_unset" not in TelegramObject.__pydantic_decorators__.model_validators

    def test_object_validates_from_json_without_intermediate_dict(self):
        # Without a before-validator pydantic can read the payload itself,
        # which is what aiogram's session relies on.
        chat = Chat.model_validate_json('{"id": -42, "type": "supergroup"}')

        assert (chat.id, chat.type) == (-42, "supergroup")


class TestTelegramMethodCall:
    async def test_async_emit_unsuccessful(self, bot: MockedBot):
        with pytest.raises(
            RuntimeError,
            match="This method is not mounted to a any bot instance.+",
        ):
            await GetMe()

    async def test_async_emit(self, bot: MockedBot):
        bot.add_result_for(GetMe, ok=True, result=User(id=42, is_bot=True, first_name="Test"))
        method = GetMe().as_(bot)
        assert isinstance(await method, User)
