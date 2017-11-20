from aiohttp import web

from . import context
from .deprecated import deprecated
from ..bot.api import log
from ..dispatcher import Dispatcher
from ..dispatcher.webhook import BOT_DISPATCHER_KEY, get_new_configured_app


async def _startup(dispatcher: Dispatcher, skip_updates=False, callback=None):
    user = await dispatcher.bot.me
    log.info(f"Bot: {user.full_name} [@{user.username}]")

    if callable(callback):
        await callback(dispatcher)

    if skip_updates:
        await dispatcher.reset_webhook(True)
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

    if dispatcher.is_polling():
        dispatcher.stop_polling()

    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


async def _wh_shutdown(app):
    callback = app.get('_shutdown_callback', None)
    dispatcher = app.get(BOT_DISPATCHER_KEY, None)
    await _shutdown(dispatcher, callback=callback)


@deprecated('The old function was renamed to `start_polling`')
def start_pooling(*args, **kwargs):
    return start_polling(*args, **kwargs)


def start_polling(dispatcher, *, loop=None, skip_updates=False, on_startup=None, on_shutdown=None):
    log.warning('Start bot with long-polling.')
    if loop is None:
        loop = dispatcher.loop

    loop.set_task_factory(context.task_factory)

    try:
        loop.run_until_complete(_startup(dispatcher, skip_updates=skip_updates, callback=on_startup))
        loop.create_task(dispatcher.start_polling(reset_webhook=True))
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        loop.run_until_complete(_shutdown(dispatcher, callback=on_shutdown))
    log.warning("Goodbye!")


def start_webhook(dispatcher, webhook_path, *, loop=None, skip_updates=None, on_startup=None, on_shutdown=None,
                  check_ip=False, **kwargs):
    log.warning('Start bot with webhook.')
    if loop is None:
        loop = dispatcher.loop

    loop.set_task_factory(context.task_factory)

    app = get_new_configured_app(dispatcher, webhook_path)
    app['_startup_callback'] = on_startup
    app['_shutdown_callback'] = on_shutdown
    app['_skip_updates'] = skip_updates
    app['_check_ip'] = check_ip

    app.on_startup.append(_wh_startup)
    app.on_shutdown.append(_wh_shutdown)

    web.run_app(app, loop=loop, **kwargs)
    return app
