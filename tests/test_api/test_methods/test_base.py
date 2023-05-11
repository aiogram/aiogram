from unittest.mock import sentinel

import pytest

from aiogram.methods import GetMe, TelegramMethod
from aiogram.types import User
from tests.mocked_bot import MockedBot


class TestTelegramMethodRemoveUnset:
    @pytest.mark.parametrize(
        "values,names",
        [
            [{}, set()],
            [{"foo": "bar"}, {"foo"}],
            [
                {
                    "foo": "bar",
                },
                {"foo"},
            ],
        ],
    )
    def test_remove_unset(self, values, names):
        import msgspec

        validated = msgspec.to_builtins(values)
        assert set(validated.keys()) == names


class TestTelegramMethodCall:
    async def test_async_emit(self, bot: MockedBot):
        bot.add_result_for(GetMe, ok=True, result=User(id=42, is_bot=True, first_name="Test"))
        assert isinstance(await GetMe(), User)
