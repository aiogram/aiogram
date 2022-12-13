import pytest
import pytest_asyncio

from aiogram import Bot, types
from . import FakeTelegram


@pytest_asyncio.fixture(name="message")
async def message_fixture(bot: Bot):
    """
    Message fixture
    :param bot: Telegram bot fixture
    :type bot: Bot
    """
    from .types.dataset import MESSAGE

    msg = types.Message(**MESSAGE)

    async with FakeTelegram(message_data=MESSAGE):
        _message = await bot.send_message(chat_id=msg.chat.id, text=msg.text)

    yield _message


class TestMiscCases:
    async def test_calling_bot_not_from_context(self, message):
        """
        Calling any helper method without bot instance in context.

        :param message: message fixture
        :type message: types.Message
        :return: RuntimeError with reason and help
        """
        with pytest.raises(RuntimeError):
            await message.edit_text('test_calling_bot_not_from_context')
