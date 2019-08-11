"""
Example outdated
"""

import asyncio
import ssl
import sys

from aiohttp import web

import aiogram
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import get_new_configured_app, SendMessage
from aiogram.types import ChatType, ParseMode, ContentTypes
from aiogram.utils.markdown import hbold, bold, text, link

TOKEN = 'BOT TOKEN HERE'

WEBHOOK_HOST = 'example.com'  # Domain name or IP addres which your bot is located.
WEBHOOK_PORT = 443  # Telegram Bot API allows only for usage next ports: 443, 80, 88 or 8443
WEBHOOK_URL_PATH = '/webhook'  # Part of URL

# This options needed if you use self-signed SSL certificate
# Instructions: https://core.telegram.org/bots/self-signed
WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

WEBHOOK_URL = f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_URL_PATH}"

# Web app settings:
#   Use LAN address to listen webhooks
#   User any available port in range from 1024 to 49151 if you're using proxy, or WEBHOOK_PORT if you're using direct webhook handling
WEBAPP_HOST = 'localhost'
WEBAPP_PORT = 3001

BAD_CONTENT = ContentTypes.PHOTO & ContentTypes.DOCUMENT & ContentTypes.STICKER & ContentTypes.AUDIO

bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def cmd_start(message: types.Message):
    # Yep. aiogram allows to respond into webhook.
    # https://core.telegram.org/bots/api#making-requests-when-getting-updates
    return SendMessage(chat_id=message.chat.id, text='Hi from webhook!',
                       reply_to_message_id=message.message_id)


async def cmd_about(message: types.Message):
    # In this function markdown utils are userd for formatting message text
    return SendMessage(message.chat.id, text(
        bold('Hi! I\'m just a simple telegram bot.'),
        '',
        text('I\'m powered by', bold('Python', Version(*sys.version_info[:]))),
        text('With', link(text('aiogram', aiogram.VERSION), 'https://github.com/aiogram/aiogram')),
        sep='\n'
    ), parse_mode=ParseMode.MARKDOWN)


async def cancel(message: types.Message):
    # Get current state context
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)

    # If current user in any state - cancel it.
    if await state.get_state() is not None:
        await state.set_state(state=None)
        return SendMessage(message.chat.id, 'Current action is canceled.')
        # Otherwise do nothing


async def unknown(message: types.Message):
    """
    Handler for unknown messages.
    """
    return SendMessage(message.chat.id,
                       f"I don\'t know what to do with content type `{message.content_type()}`. Sorry :c")


async def cmd_id(message: types.Message):
    """
    Return info about user.
    """
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        chat = message.chat
    elif message.forward_from and message.chat.type == ChatType.PRIVATE:
        target = message.forward_from
        chat = message.forward_from or message.chat
    else:
        target = message.from_user
        chat = message.chat

    result_msg = [hbold('Info about user:'),
                  f"First name: {target.first_name}"]
    if target.last_name:
        result_msg.append(f"Last name: {target.last_name}")
    if target.username:
        result_msg.append(f"Username: {target.mention}")
    result_msg.append(f"User ID: {target.id}")

    result_msg.extend([hbold('Chat:'),
                       f"Type: {chat.type}",
                       f"Chat ID: {chat.id}"])
    if chat.type != ChatType.PRIVATE:
        result_msg.append(f"Title: {chat.title}")
    else:
        result_msg.append(f"Title: {chat.full_name}")
    return SendMessage(message.chat.id, '\n'.join(result_msg), reply_to_message_id=message.message_id,
                       parse_mode=ParseMode.HTML)


async def on_startup(app):
    # Demonstrate one of the available methods for registering handlers
    # This command available only in main state (state=None)
    dp.register_message_handler(cmd_start, commands=['start'])

    # This handler is available in all states at any time.
    dp.register_message_handler(cmd_about, commands=['help', 'about'], state='*')
    dp.register_message_handler(unknown, content_types=BAD_CONTENT,
                                func=lambda message: message.chat.type == ChatType.PRIVATE)

    # You are able to register one function handler for multiple conditions
    dp.register_message_handler(cancel, commands=['cancel'], state='*')
    dp.register_message_handler(cancel, func=lambda message: message.text.lower().strip() in ['cancel'], state='*')

    dp.register_message_handler(cmd_id, commands=['id'], state='*')
    dp.register_message_handler(cmd_id, func=lambda message: message.forward_from or
                                                             message.reply_to_message and
                                                             message.chat.type == ChatType.PRIVATE, state='*')

    # Get current webhook status
    webhook = await bot.get_webhook_info()

    # If URL is bad
    if webhook.url != WEBHOOK_URL:
        # If URL doesnt match current - remove webhook
        if not webhook.url:
            await bot.delete_webhook()

        # Set new URL for webhook
        await bot.set_webhook(WEBHOOK_URL, certificate=open(WEBHOOK_SSL_CERT, 'rb'))
        # If you want to use free certificate signed by LetsEncrypt you need to set only URL without sending certificate.


async def on_shutdown(app):
    """
    Graceful shutdown. This method is recommended by aiohttp docs.
    """
    # Remove webhook.
    await bot.delete_webhook()

    # Close Redis connection.
    await dp.storage.close()
    await dp.storage.wait_closed()


if __name__ == '__main__':
    # Get instance of :class:`aiohttp.web.Application` with configured router.
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)

    # Setup event handlers.
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Generate SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

    # Start web-application.
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT, ssl_context=context)
    # Note:
    #   If you start your bot using nginx or Apache web server, SSL context is not required.
    #   Otherwise you need to set `ssl_context` parameter.
