import asyncio
import datetime
import functools
import secrets
from warnings import warn

from aiohttp import web

from . import context
from ..bot.api import log
from ..dispatcher.webhook import BOT_DISPATCHER_KEY, WebhookRequestHandler

APP_EXECUTOR_KEY = 'APP_EXECUTOR'


def _setup_callbacks(executor, on_startup=None, on_shutdown=None):
    if on_startup is not None:
        executor.on_startup(on_startup)
    if on_shutdown is not None:
        executor.on_shutdown(on_shutdown)


def start_polling(dispatcher, *, loop=None, skip_updates=False, reset_webhook=True,
                  on_startup=None, on_shutdown=None, timeout=None):
    """
    Start bot in long-polling mode

    :param dispatcher:
    :param loop:
    :param skip_updates:
    :param reset_webhook:
    :param on_startup:
    :param on_shutdown:
    :param timeout:
    """
    executor = Executor(dispatcher, skip_updates=skip_updates, loop=loop)
    _setup_callbacks(executor, on_startup, on_shutdown)

    executor.start_polling(reset_webhook=reset_webhook, timeout=timeout)


def start_webhook(dispatcher, webhook_path, *, loop=None, skip_updates=None,
                  on_startup=None, on_shutdown=None, check_ip=False, **kwargs):
    """
    Start bot in webhook mode

    :param dispatcher:
    :param webhook_path:
    :param loop:
    :param skip_updates:
    :param on_startup:
    :param on_shutdown:
    :param check_ip:
    :param kwargs:
    :return:
    """
    executor = Executor(dispatcher, skip_updates=skip_updates, check_ip=check_ip, loop=loop)
    _setup_callbacks(executor, on_startup, on_shutdown)

    executor.start_webhook(webhook_path, **kwargs)


def start(dispatcher, future, *, loop=None, skip_updates=None,
          on_startup=None, on_shutdown=None):
    """
    Execute Future.

    :param dispatcher: instance of Dispatcher
    :param future: future
    :param loop: instance of AbstractEventLoop
    :param skip_updates:
    :param on_startup:
    :param on_shutdown:
    :return:
    """
    executor = Executor(dispatcher, skip_updates=skip_updates, loop=loop)
    _setup_callbacks(executor, on_startup, on_shutdown)

    return executor.start(future)


class Executor:
    """
    Main executor class
    """

    def __init__(self, dispatcher, skip_updates=None, check_ip=False, loop=None):
        if loop is None:
            loop = dispatcher.loop
        self.dispatcher = dispatcher
        self.skip_updates = skip_updates
        self.check_ip = check_ip
        self.loop = loop

        self._identity = secrets.token_urlsafe(16)
        self._web_app = None

        self._on_startup_webhook = []
        self._on_startup_polling = []
        self._on_shutdown_webhook = []
        self._on_shutdown_polling = []

        self._freeze = False

    @property
    def frozen(self):
        return self._freeze

    def set_web_app(self, application: web.Application):
        """
        Change instance of aiohttp.web.Applicaton

        :param application:
        """
        self._web_app = application

    @property
    def web_app(self) -> web.Application:
        if self._web_app is None:
            raise RuntimeError('web.Application() is not configured!')
        return self._web_app

    def on_startup(self, callback: callable, polling=True, webhook=True):
        """
        Register a callback for the startup process

        :param callback:
        :param polling: use with polling
        :param webhook: use with webhook
        """
        self._check_frozen()
        if not webhook and not polling:
            warn('This action has no effect!', UserWarning)
            return

        if isinstance(callback, (list, tuple, set)):
            for cb in callback:
                self.on_startup(cb, polling, webhook)
            return

        if polling:
            self._on_startup_polling.append(callback)
        if webhook:
            self._on_startup_webhook.append(callback)

    def on_shutdown(self, callback: callable, polling=True, webhook=True):
        """
        Register a callback for the shutdown process

        :param callback:
        :param polling: use with polling
        :param webhook: use with webhook
        """
        self._check_frozen()
        if not webhook and not polling:
            warn('This action has no effect!', UserWarning)
            return

        if isinstance(callback, (list, tuple, set)):
            for cb in callback:
                self.on_shutdown(cb, polling, webhook)
            return

        if polling:
            self._on_shutdown_polling.append(callback)
        if webhook:
            self._on_shutdown_webhook.append(callback)

    def _check_frozen(self):
        if self.frozen:
            raise RuntimeError('Executor is frozen!')

    def _prepare_polling(self):
        self._check_frozen()
        self._freeze = True

        self.loop.set_task_factory(context.task_factory)

    def _prepare_webhook(self, path=None, handler=WebhookRequestHandler):
        self._check_frozen()
        self._freeze = True

        self.loop.set_task_factory(context.task_factory)

        app = self._web_app
        if app is None:
            self._web_app = app = web.Application()

        if self._identity == app.get(self._identity):
            # App is already configured
            return

        if path is not None:
            app.router.add_route('*', path, handler, name='webhook_handler')

        async def _wrap_callback(cb, _):
            return await cb(self.dispatcher)

        for callback in self._on_startup_webhook:
            app.on_startup.append(functools.partial(_wrap_callback, callback))
        # for callback in self._on_shutdown_webhook:
        #     app.on_shutdown.append(functools.partial(_wrap_callback, callback))

        async def _on_shutdown(_):
            await self._shutdown_webhook()

        app.on_shutdown.append(_on_shutdown)
        app[APP_EXECUTOR_KEY] = self
        app[BOT_DISPATCHER_KEY] = self.dispatcher
        app[self._identity] = datetime.datetime.now()
        app['_check_ip'] = self.check_ip

    def start_webhook(self, webhook_path=None, request_handler=WebhookRequestHandler, **kwargs):
        """
        Start bot in webhook mode

        :param webhook_path:
        :param request_handler:
        :param kwargs:
        :return:
        """
        self._prepare_webhook(webhook_path, request_handler)
        self.loop.run_until_complete(self._startup_webhook())

        web.run_app(self._web_app, **kwargs)

    def start_polling(self, reset_webhook=None, timeout=None):
        """
        Start bot in long-polling mode

        :param reset_webhook:
        :param timeout:
        """
        self._prepare_polling()
        loop: asyncio.AbstractEventLoop = self.loop

        try:
            loop.run_until_complete(self._startup_polling())
            loop.create_task(self.dispatcher.start_polling(reset_webhook=reset_webhook, timeout=timeout))
            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            # loop.stop()
            pass
        finally:
            loop.run_until_complete(self._shutdown_polling())
        log.warning("Goodbye!")

    def start(self, future):
        """
        Execute Future.

        Return the Future's result, or raise its exception.

        :param future:
        :return:
        """
        self._check_frozen()
        self._freeze = True
        loop: asyncio.AbstractEventLoop = self.loop

        try:
            loop.run_until_complete(self._startup_polling())
            result = loop.run_until_complete(future)
        except (KeyboardInterrupt, SystemExit):
            result = None
            loop.stop()
        finally:
            loop.run_until_complete(self._shutdown_polling())
        log.warning("Goodbye!")
        return result

    async def _skip_updates(self):
        await self.dispatcher.reset_webhook(True)
        count = await self.dispatcher.skip_updates()
        if count:
            log.warning(f"Skipped {count} updates.")
        return count

    async def _welcome(self):
        user = await self.dispatcher.bot.me
        log.info(f"Bot: {user.full_name} [@{user.username}]")

    async def _shutdown(self):
        self.dispatcher.stop_polling()
        await self.dispatcher.storage.close()
        await self.dispatcher.storage.wait_closed()
        await self.dispatcher.bot.close()

    async def _startup_polling(self):
        await self._welcome()

        if self.skip_updates:
            await self._skip_updates()
        for callback in self._on_startup_polling:
            await callback(self.dispatcher)

    async def _shutdown_polling(self, wait_closed=False):
        await self._shutdown()

        for callback in self._on_shutdown_polling:
            await callback(self.dispatcher)

        if wait_closed:
            await self.dispatcher.wait_closed()

    async def _shutdown_webhook(self, wait_closed=False):
        for callback in self._on_shutdown_webhook:
            await callback(self.dispatcher)

        await self._shutdown()

        if wait_closed:
            await self.dispatcher.wait_closed()

    async def _startup_webhook(self):
        await self._welcome()
        if self.skip_updates:
            self._skip_updates()
