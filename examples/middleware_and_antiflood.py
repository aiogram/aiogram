import asyncio

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher import CancelHandler, DEFAULT_RATE_LIMIT, Dispatcher, ctx
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils import context, executor
from aiogram.utils.exceptions import Throttled

TOKEN = 'BOT TOKEN HERE'

loop = asyncio.get_event_loop()

# In this example used Redis storage
storage = RedisStorage2(db=5)

bot = Bot(token=TOKEN, loop=loop)
dp = Dispatcher(bot, storage=storage)


def rate_limit(limit: int, key=None):
    """
    Decorator for configuring rate limit and key in different functions.

    :param limit:
    :param key:
    :return:
    """

    def decorator(func):
        setattr(func, 'throttling_rate_limit', limit)
        if key:
            setattr(func, 'throttling_key', key)
        return func

    return decorator


class ThrottlingMiddleware(BaseMiddleware):
    """
    Simple middleware
    """

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message):
        """
        That handler will be called when dispatcher receive message

        :param message:
        """
        # Get current handler
        handler = context.get_value('handler')

        # Get dispatcher from context
        dispatcher = ctx.get_dispatcher()

        # If handler was configured get  rate limit and key from handler
        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        # Use Dispatcher.throttle method.
        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            # Execute action
            await self.message_throttled(message, t)

            # Cancel current handler
            raise CancelHandler()

    async def message_throttled(self, message: types.Message, throttled: Throttled):
        """
        Notify user only on first exceed and notify about unlocking only on last exceed

        :param message:
        :param throttled:
        """
        handler = context.get_value('handler')
        dispatcher = ctx.get_dispatcher()
        if handler:
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"

        # Calculate how many time left to the end of block.
        delta = throttled.rate - throttled.delta

        # Prevent flooding
        if throttled.exceeded_count <= 2:
            await message.reply('Too many requests! ')

        # Sleep.
        await asyncio.sleep(delta)

        # Check lock status
        thr = await dispatcher.check_key(key)

        # If current message is not last with current key - do not send message
        if thr.exceeded_count == throttled.exceeded_count:
            await message.reply('Unlocked.')


@dp.message_handler(commands=['start'])
@rate_limit(5, 'start')  # is not required but with that you can configure throttling manager for current handler
async def cmd_test(message: types.Message):
    # You can use that command every 5 seconds
    await message.reply('Test passed! You can use that command every 5 seconds.')


if __name__ == '__main__':
    # Setup middleware
    dp.middleware.setup(ThrottlingMiddleware())

    # Start long-polling
    executor.start_polling(dp, loop=loop)
