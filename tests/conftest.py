import pytest

from aiogram import Bot
from tests.mocked_bot import MockedBot


@pytest.fixture()
def bot():
    bot = MockedBot()
    token = Bot.set_current(bot)
    yield bot
    Bot.reset_current(token)
    bot.me.invalidate(bot)
