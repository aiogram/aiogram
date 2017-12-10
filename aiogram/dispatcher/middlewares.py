import logging
import typing

log = logging.getLogger('aiogram.Middleware')


class MiddlewareManager:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.loop = dispatcher.loop
        self.bot = dispatcher.bot
        self.storage = dispatcher.storage
        self.applications = []

    def setup(self, middleware):
        """
        Setup middleware

        :param middleware:
        :return:
        """
        assert isinstance(middleware, BaseMiddleware)
        if middleware.is_configured():
            raise ValueError('That middleware is already used!')

        self.applications.append(middleware)
        middleware.setup(self)
        log.debug(f"Loaded middleware '{middleware.__class__.__name__}'")

    async def trigger(self, action: str, args: typing.Iterable):
        """
        Call action to middlewares with args lilt.

        :param action:
        :param args:
        :return:
        """
        for app in self.applications:
            await app.trigger(action, args)


class BaseMiddleware:
    def __init__(self):
        self._configured = False
        self._manager = None

    @property
    def manager(self) -> MiddlewareManager:
        if self._manager is None:
            raise RuntimeError('Middleware is not configured!')
        return self._manager

    def setup(self, manager):
        self._manager = manager
        self._configured = True

    def is_configured(self):
        return self._configured

    async def trigger(self, action, args):
        handler_name = f"on_{action}"
        handler = getattr(self, handler_name, None)
        if not handler:
            return None
        await handler(*args)
