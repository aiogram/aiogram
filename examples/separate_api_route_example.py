# NOTE: This is an example of an integration between 
# externally created Application object and the aiogram's dispatcher
# This can be used for a custom route, for instance

from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.webhook import configure_app
from aiohttp import web


bot = Bot(token=config.bot_token)
dp = Dispatcher(bot)



@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("start!")


# handle /api route
async def api_handler(request):
    return web.json_response({"status": "OK"}, status=200)


app = web.Application()
# add a custom route
app.add_routes([web.post('/api', api_handler)])
# every request to /bot route will be retransmitted to dispatcher to be handled
# as a bot update
configure_app(dp, app, "/bot")


if __name__ == '__main__':
    web.run_app(app, port=9000)
