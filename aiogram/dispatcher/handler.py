from .filters import check_filters


class Handler:
    def __init__(self, dispatcher, once=True):
        self.dispatcher = dispatcher
        self.once = once

        self.handlers = []

    def register(self, handler, filters=None):
        if filters and not isinstance(filters, (list, tuple, set)):
            filters = [filters]
        self.handlers.append((filters, handler))

    def unregister(self, handler):
        for handler_with_filters in self.handlers:
            _, registered = handler_with_filters
            if handler is registered:
                self.handlers.remove(handler_with_filters)
                return True
        raise ValueError('This handler is not registered!')

    async def notify(self, *args, **kwargs):
        for filters, handler in self.handlers:
            if await check_filters(filters, args, kwargs):
                await handler(*args, **kwargs)
                if self.once:
                    break
