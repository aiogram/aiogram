from aiogram import Bot, types
from aiogram.contrib.middlewares.context import ContextMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import markdown as md
from aiogram.utils.executor import start_polling

API_TOKEN = 'BOT TOKEN HERE'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Setup Context middleware
data: ContextMiddleware = dp.middleware.setup(ContextMiddleware())


# Write custom filter
async def demo_filter(message: types.Message):
    # Store some data in context
    command = data['command'] = message.get_command() or ''
    args = data['args'] = message.get_args() or ''
    data['has_args'] = bool(args)
    data['some_random_data'] = 42
    return command != '/bad_command'


@dp.message_handler(demo_filter)
async def send_welcome(message: types.Message):
    # Get data from context
    # All of that available only in current context and from current update object
    # `data`- pseudo-alias for `ctx.get_update().conf['_context_data']`
    command = data['command']
    args = data['args']
    rand = data['some_random_data']
    has_args = data['has_args']

    # Send as pre-formatted code block.
    await message.reply(md.hpre(f"""command: {command}
args: {['Not available', 'available'][has_args]}: {args}
some random data: {rand}
message ID: {message.message_id}
message: {message.html_text}
    """), parse_mode=ParseMode.HTML)


if __name__ == '__main__':
    start_polling(dp)
