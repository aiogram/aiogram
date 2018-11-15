from asyncio import BaseEventLoop

import pytest

from aiogram import Bot, types, Dispatcher
from aiogram.dispatcher.handler import Handler

pytestmark = pytest.mark.asyncio
TOKEN = '123456789:AABBCCDDEEFFaabbccddeeff-1234567890'


@pytest.yield_fixture()
async def bot(event_loop: BaseEventLoop):
    """ Bot fixture """
    _bot = Bot(TOKEN, loop=event_loop, parse_mode=types.ParseMode.HTML)
    yield _bot
    await _bot.close()


@pytest.yield_fixture()
async def dp(event_loop: BaseEventLoop, bot: Bot):
    """
    Dispatcher fixture
    :rtype: Dispatcher
    """
    _dp = Dispatcher(bot=bot, loop=event_loop)
    yield _dp


class TestErrorsHandlerArgs:
    @staticmethod
    def get_handler_from(handler_category: Handler):
        filters, handler = handler_category.handlers.pop()
        return handler

    def method_with_3_args(self, two, three):
        pass

    def method_with_4_args(self, two, three, four):
        pass

    def method_with_varargs(self, two, three, *args):
        pass

    def method_with_varkw(self, two, three, **kwargs):
        pass

    def method_with_varargs_and_varkw(self, two, three, *args, **kwargs):
        pass

    async def test_errors_handler_func_with_2_args(self, dp: Dispatcher):
        """ Test handler as func with 2 args """

        async def func(one, two):
            pass

        dp.register_errors_handler(func)
        assert func == self.get_handler_from(dp.errors_handlers)

    async def test_errors_handler_func_with_3_args(self, dp: Dispatcher):
        """ Test handler with 3 args """

        async def func(one, two, three):
            pass

        with pytest.raises(RuntimeError):
            dp.register_errors_handler(func)

        assert len(dp.errors_handlers.handlers) == 0

    async def test_errors_handler_method_with_3_args(self, dp: Dispatcher):
        """ Test handler as class method with 3 args """

        dp.register_errors_handler(self.method_with_3_args)
        assert self.method_with_3_args == self.get_handler_from(dp.errors_handlers)

    async def test_errors_handler_method_with_4_args(self, dp: Dispatcher):
        """ Test handler as class method with 4 args """

        with pytest.raises(RuntimeError):
            dp.register_errors_handler(self.method_with_4_args)

    async def test_errors_handler_method_with_varargs(self, dp: Dispatcher):
        """ Test handler as class method with 2 args (except self) and *args """

        dp.register_errors_handler(self.method_with_varargs)
        assert self.method_with_varargs == self.get_handler_from(dp.errors_handlers)

    async def test_errors_handler_method_with_varkw(self, dp: Dispatcher):
        """ Test handler as class method with 2 args (except self) and **kwargs """

        dp.register_errors_handler(self.method_with_varkw)
        assert self.method_with_varkw == self.get_handler_from(dp.errors_handlers)

    async def test_errors_handler_method_with_varargs_and_varkw(self, dp: Dispatcher):
        """ Test handler as class method with 2 args (except self), *args and **kwargs """

        dp.register_errors_handler(self.method_with_varargs_and_varkw)
        assert self.method_with_varargs_and_varkw == self.get_handler_from(dp.errors_handlers)
