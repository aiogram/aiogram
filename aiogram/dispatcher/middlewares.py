from . import Handler
from .handler import SkipHandler


class Middleware:
    def __init__(self, handler, filters=None):
        self.handler: Handler = handler
        self.configure_handler(filters)

    def configure_handler(self, filters):
        if filters is None:
            filters = []
        self.handler.register(self._handle_event, filters, 0)

    async def handle(self, *args, **kwargs):
        raise NotImplementedError

    async def check_data(self, *args, **kwargs):
        return True

    async def _handle_event(self, *args, **kwargs):
        if await self.check_data(*args, **kwargs):
            await self.handle(*args, **kwargs)
        raise SkipHandler()
