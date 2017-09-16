import asyncio

from aiohttp import web

from aiogram.bot.api import log
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import BOT_DISPATCHER_KEY, get_new_configured_app
from aiogram.utils import context


async def _startup(dispatcher: Dispatcher, skip_updates=False, callback=None):
    user = await dispatcher.bot.me
    log.info(f"Bot: {user.full_name} [@{user.username}]")

    if callable(callback):
        await callback(dispatcher)

    if skip_updates:
        count = await dispatcher.skip_updates()
        if count:
            log.warning(f"Skipped {count} updates.")


async def _wh_startup(app):
    callback = app.get('_startup_callback', None)
    dispatcher = app.get(BOT_DISPATCHER_KEY, None)
    skip_updates = app.get('_skip_updates', False)
    await _startup(dispatcher, skip_updates=skip_updates, callback=callback)


async def _shutdown(dispatcher: Dispatcher, callback=None):
    if callable(callback):
        await callback(dispatcher)

    dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


async def _wh_shutdown(app):
    callback = app.get('_shutdown_callback', None)
    dispatcher = app.get(BOT_DISPATCHER_KEY, None)
    await _shutdown(dispatcher, callback=callback)


def start_pooling(dispatcher, *, loop=None, skip_updates=False, on_startup=None, on_shutdown=None):
    log.warning('Start bot with long-pooling.')
    if loop is None:
        loop = asyncio.get_event_loop()

    loop.set_task_factory(context.task_factory)

    loop.create_task(dispatcher.start_pooling())
    try:
        loop.run_until_complete(_startup(dispatcher, skip_updates=skip_updates, callback=on_startup))
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        loop.run_until_complete(_shutdown(dispatcher, callback=on_shutdown))
    log.warning("Goodbye!")


def start_webhook(dispatcher, webhook_path, *, loop=None, skip_updates=None, on_startup=None, on_shutdown=None,
                  **kwargs):
    log.warning('Start bot with webhook.')
    if loop is None:
        loop = asyncio.get_event_loop()

    app = get_new_configured_app(dispatcher, webhook_path)
    app['_startup_callback'] = on_startup
    app['_shutdown_callback'] = on_shutdown
    app['_skip_updates'] = skip_updates

    app.on_startup.append(_wh_startup)
    app.on_shutdown.append(_wh_shutdown)

    web.run_app(app, loop=loop, **kwargs)
