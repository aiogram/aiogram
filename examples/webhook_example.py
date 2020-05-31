import logging
import ssl

from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook


API_TOKEN = 'Your bot token'

# webserver settings
WEBAPP_HOST = 'localhost'  # or 0.0.0.0
WEBAPP_PORT = 88

# SSL settings
WEBHOOK_SSL_CERT = 'path_to_cert.pem'
WEBHOOK_SSL_PRIV = 'path_to_private.key'

# webhook settings
WEBHOOK_HOST = 'XX.XX.XX.XX'  # IP your host
WEBHOOK_PORT = 88  # Ports currently supported for Webhooks: 443, 80, 88, 8443
WEBHOOK_PATH = '/bot'
WEBHOOK_URL = f'{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_PATH}'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler()
async def echo(message: types.Message):
    # Regular request
    # await bot.send_message(message.chat.id, message.text)

    # or reply INTO webhook
    return SendMessage(message.chat.id, message.text)


async def on_startup(dp):
    logging.warning('Webhook startup..')

    # Check webhook
    webhook = await bot.get_webhook_info()

    # If webhook URL doesnt match current - remove webhook
    if webhook.url != WEBHOOK_URL:
        await bot.delete_webhook()

        # Set webhook
        await bot.set_webhook(WEBHOOK_URL, certificate=open(WEBHOOK_SSL_CERT, 'rb').read())
    # insert code here to run it after start


async def on_shutdown(dp):
    logging.warning('Shutting down..')
    await bot.close()
    # insert code here to run it before shutdown

    # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning('Bye!')


if __name__ == '__main__':

    # Generate SSL context.
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        ssl_context=context
    )
