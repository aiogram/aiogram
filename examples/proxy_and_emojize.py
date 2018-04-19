import asyncio
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils.emoji import emojize
from aiogram.utils.executor import start_polling
from aiogram.utils.markdown import bold, code, italic, text

# Configure bot here
API_TOKEN = 'BOT TOKEN HERE'
PROXY_URL = 'http://PROXY_URL'

# If authentication is required in your proxy then uncomment next line and change login/password for it
# PROXY_AUTH = aiohttp.BasicAuth(login='login', password='password')
# And add `proxy_auth=PROXY_AUTH` argument in line 25, like this:
# >>> bot = Bot(token=API_TOKEN, loop=loop, proxy=PROXY_URL, proxy_auth=PROXY_AUTH)

# Get my ip URL
GET_IP_URL = 'http://bot.whatismyipaddress.com/'

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop, proxy=PROXY_URL)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # Create a temporary session
    session = bot.create_temp_session()

    content = []

    # Make request (without proxy)
    async with session.get(GET_IP_URL) as response:
        content.append(text(':globe_showing_Americas:', bold('IP:'), code(await response.text())))
        # This line is formatted to '🌎 *IP:* `YOUR IP`'

    # Make request through proxy
    async with session.get(GET_IP_URL, proxy=bot.proxy, proxy_auth=bot.proxy_auth) as response:
        content.append(text(':locked_with_key:', bold('IP:'), code(await response.text()), italic('via proxy')))
        # This line is formatted to '🔐 *IP:* `YOUR IP` _via proxy_'

    # Send content
    await bot.send_message(message.chat.id, emojize(text(*content, sep='\n')), parse_mode=ParseMode.MARKDOWN)

    # Destroy temp session
    await bot.destroy_temp_session(session)

    # In this example you can see emoji codes: ":globe_showing_Americas:" and ":locked_with_key:"
    # You can find full emoji cheat sheet at https://www.webpagefx.com/tools/emoji-cheat-sheet/
    # For representing emoji codes into real emoji use emoji util (aiogram.utils.emoji)
    # (you have to install emoji module)

    # For example emojize('Moon face :new_moon_face:') is transformed to 'Moon face 🌚'


if __name__ == '__main__':
    start_polling(dp, loop=loop, skip_updates=True)
