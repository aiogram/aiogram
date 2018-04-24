import asyncio
import logging

from aiohttp import ClientSession
from aiosocksy.connector import ProxyConnector, ProxyClientRequest

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils.executor import start_polling
from aiogram.utils.markdown import bold, code, italic, text

# Configure bot here
API_TOKEN = '<BOT TOKEN>'
PROXY_URL = 'socks5://...'
# If authentication is required in your proxy then uncomment next line and change login/password for it
# PROXY_AUTH = aiosocksy.Socks5Auth(login='login', password='password')
# And add `proxy_auth=PROXY_AUTH` argument in line 25, like this:
# >>> bot = Bot(token=API_TOKEN, loop=loop, proxy=PROXY_URL, proxy_auth=PROXY_AUTH)

# Get my ip URL
GET_IP_URL = 'http://bot.whatismyipaddress.com/'

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop, proxy=PROXY_URL, proxy_auth=PROXY_AUTH)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    content = []

    # Make request (without proxy)
    async with ClientSession() as session:
        async with session.get(GET_IP_URL) as response:
            content.append(text('🌎', bold('IP:'), code(await response.text())))

    # Make request through proxy
    async with ClientSession(connector=ProxyConnector(), request_class=ProxyClientRequest) as session:
        async with session.get(GET_IP_URL, proxy=bot.proxy, proxy_auth=bot.proxy_auth) as response:
            content.append(text('🔐', bold('IP:'), code(await response.text()), italic('via proxy')))

    await bot.send_message(message.chat.id, text(*content, sep='\n'), parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
    start_polling(dp, loop=loop, skip_updates=True)
