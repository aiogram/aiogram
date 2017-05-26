import inspect


async def check_filter(filter_, args, kwargs):
    if inspect.iscoroutinefunction(filter_):
        return await filter_(*args, **kwargs)
    elif callable(filter_):
        return filter_(*args, **kwargs)
    else:
        return True


async def check_filters(filters, args, kwargs):
    if filters is not None:
        for filter_ in filters:
            f = await check_filter(filter_, args, kwargs)
            if not f:
                return False
    return True


class Handler:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

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
