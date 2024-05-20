from typing import Any, Dict
from unittest.mock import sentinel

import pytest

from aiogram.client.default import Default
from aiogram.methods import GetMe, SendMessage, TelegramMethod
from aiogram.types import LinkPreviewOptions, TelegramObject, User
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
        validated = obj.remove_unset.wrapped(values)
        assert set(validated.keys()) == names

    @pytest.mark.parametrize("obj", [TelegramMethod, TelegramObject])
    def test_remove_unset_non_dict(self, obj):
        assert obj.remove_unset.wrapped("") == ""


class TestTelegramMethodModelDumpJson:
    @pytest.mark.parametrize(
        "obj",
        [
            SendMessage(
                chat_id=1,
                text="test",
            ),
            LinkPreviewOptions(),
        ],
    )
    def test_model_dump_json(self, obj):
        def has_defaults(dump: Dict[str, Any]) -> bool:
            return any(isinstance(value, Default) for value in dump.values())

        assert has_defaults(obj.model_dump())
        assert not has_defaults(obj.model_dump(mode="json"))


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
