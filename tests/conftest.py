import pytest

from aiogram import Bot
from tests.mocked_bot import MockedBot


@pytest.fixture()
def bot():
    bot = MockedBot()
    Bot.set_current(bot)
    yield bot
