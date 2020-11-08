import pytest

from aiogram import Bot, Dispatcher

pytestmark = pytest.mark.asyncio


@pytest.yield_fixture()
async def bot(event_loop):
    """ Bot fixture """
    _bot = Bot(token='123456789:AABBCCDDEEFFaabbccddeeff-1234567890',
               loop=event_loop)
    yield _bot
    await _bot.close()


class TestDispatcherInit:
    async def test_successful_init(self, bot):
        """
        Success __init__ case

        :param bot: bot instance
        :type bot: Bot
        """
        dp = Dispatcher(bot=bot)
        assert isinstance(dp, Dispatcher)

    @pytest.mark.parametrize("bot_instance", [None, Bot, 123, 'abc'])
    async def test_wrong_bot_instance(self, bot_instance):
        """
        User provides wrong data to 'bot' argument.
        :return: TypeError with reason
        """
        with pytest.raises(TypeError):
            _ = Dispatcher(bot=bot_instance)
