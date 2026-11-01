import pytest

from aiogram.client.default import Default
from aiogram.methods import GetMe, SendMessage, TelegramMethod
from aiogram.types import Chat, TelegramObject, User
from tests.mocked_bot import MockedBot


class TestNoBeforeValidator:
    # UNSET stopped reaching model initialization in #1392, when bot-wide defaults
    # were reworked onto Default(...) sentinels. The before-validator that stripped
    # it is gone, so pydantic can read a payload straight into the model.
    @pytest.mark.parametrize("obj", [TelegramMethod, TelegramObject])
    def test_no_before_validator_is_registered(self, obj):
        assert obj.__pydantic_decorators__.model_validators == {}

    def test_type_validates_from_json(self):
        chat = Chat.model_validate_json('{"id": -42, "type": "supergroup"}')

        assert (chat.id, chat.type) == (-42, "supergroup")

    def test_method_validates_from_json(self):
        method = SendMessage.model_validate_json('{"chat_id": -42, "text": "test"}')

        assert (method.chat_id, method.text) == (-42, "test")

    def test_declared_defaults_still_apply(self):
        method = SendMessage.model_validate({"chat_id": 42, "text": "test"})

        assert method.parse_mode == Default("parse_mode")


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
