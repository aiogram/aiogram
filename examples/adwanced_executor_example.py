#!/usr/bin/env python3
"""
**This example is outdated**
In this example used ArgumentParser for configuring Your bot.

Provided to start bot with webhook:
    python adwanced_executor_example.py \
        --token TOKEN_HERE \
        --host 0.0.0.0 \
        --port 8084 \
        --host-name example.com \
        --webhook-port 443

Or long polling:
    python adwanced_executor_example.py --token TOKEN_HERE

So... In this example found small trouble:
    can't get bot instance in handlers.


If you want to automatic change getting updates method use executor utils (from aiogram.utils.executor)
"""
# TODO: Move token to environment variables.

import argparse
import logging
import ssl
import sys

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import *
from aiogram.utils.executor import start_polling, start_webhook

logging.basicConfig(level=logging.INFO)

# Configure arguments parser.
parser = argparse.ArgumentParser(description='Python telegram bot')
parser.add_argument('--token', '-t', nargs='?', type=str, default=None, help='Set working directory')
parser.add_argument('--sock', help='UNIX Socket path')
parser.add_argument('--host', help='Webserver host')
parser.add_argument('--port', type=int, help='Webserver port')
parser.add_argument('--cert', help='Path to SSL certificate')
parser.add_argument('--pkey', help='Path to SSL private key')
parser.add_argument('--host-name', help='Set webhook host name')
parser.add_argument('--webhook-port', type=int, help='Port for webhook (default=port)')
parser.add_argument('--webhook-path', default='/webhook', help='Port for webhook (default=port)')


async def cmd_start(message: types.Message):
    return SendMessage(message.chat.id, f"Hello, {message.from_user.full_name}!")


def setup_handlers(dispatcher: Dispatcher):
    # This example has only one messages handler
    dispatcher.register_message_handler(cmd_start, commands=['start', 'welcome'])


async def on_startup(dispatcher, url=None, cert=None):
    setup_handlers(dispatcher)

    bot = dispatcher.bot

    # Get current webhook status
    webhook = await bot.get_webhook_info()

    if url:
        # If URL is bad
        if webhook.url != url:
            # If URL doesnt match with by current remove webhook
            if not webhook.url:
                await bot.delete_webhook()

            # Set new URL for webhook
            if cert:
                with open(cert, 'rb') as cert_file:
                    await bot.set_webhook(url, certificate=cert_file)
            else:
                await bot.set_webhook(url)
    elif webhook.url:
        # Otherwise remove webhook.
        await bot.delete_webhook()


async def on_shutdown(dispatcher):
    print('Shutdown.')


def main(arguments):
    args = parser.parse_args(arguments)
    token = args.token
    sock = args.sock
    host = args.host
    port = args.port
    cert = args.cert
    pkey = args.pkey
    host_name = args.host_name or host
    webhook_port = args.webhook_port or port
    webhook_path = args.webhook_path

    # Fi webhook path
    if not webhook_path.startswith('/'):
        webhook_path = '/' + webhook_path

    # Generate webhook URL
    webhook_url = f"https://{host_name}:{webhook_port}{webhook_path}"

    # Create bot & dispatcher instances.
    bot = Bot(token)
    dispatcher = Dispatcher(bot)

    if (sock or host) and host_name:
        if cert and pkey:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            ssl_context.load_cert_chain(cert, pkey)
        else:
            ssl_context = None

        start_webhook(dispatcher, webhook_path,
                      on_startup=functools.partial(on_startup, url=webhook_url, cert=cert),
                      on_shutdown=on_shutdown,
                      host=host, port=port, path=sock, ssl_context=ssl_context)
    else:
        start_polling(dispatcher, on_startup=on_startup, on_shutdown=on_shutdown)


if __name__ == '__main__':
    argv = sys.argv[1:]

    if not len(argv):
        parser.print_help()
        sys.exit(1)

    main(argv)
