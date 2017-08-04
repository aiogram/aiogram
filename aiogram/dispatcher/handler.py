from .filters import check_filters


class SkipHandler(BaseException):
    pass


class CancelHandler(BaseException):
    pass


class Handler:
    def __init__(self, dispatcher, once=True):
        self.dispatcher = dispatcher
        self.once = once

        self.handlers = []

    def register(self, handler, filters=None, index=None):
        if filters and not isinstance(filters, (list, tuple, set)):
            filters = [filters]
        record = (filters, handler)
        if index is None:
            self.handlers.append(record)
        else:
            self.handlers.insert(index, record)

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
                try:
                    await handler(*args, **kwargs)
                    if self.once:
                        break
                except SkipHandler:
                    continue
                except CancelHandler:
                    break
