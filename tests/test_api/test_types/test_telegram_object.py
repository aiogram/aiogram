import pytest

from aiogram import Bot
from aiogram.api.types import TelegramObject


class TestTelegramObject:
    @pytest.fixture()
    def context_cleanup(self):
        yield
        Bot.reset_current(self.__token)

    @pytest.mark.usefixtures("context_cleanup")
    def test_bot_property_positive(self):
        self.__token = Bot.set_current(Bot("42:TEST"))

        assert isinstance(TelegramObject().bot, Bot)

    def test_bot_property_negative(self):
        with pytest.raises(RuntimeError, match=r"Bot.set_current\(bot_instance\)"):
            isinstance(TelegramObject().bot, Bot)
