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
        """
        Register callback

        Filters can be awaitable or not.

        :param handler: coroutine
        :param filters: list of filters
        :param index: you can reorder handlers
        """
        if filters and not isinstance(filters, (list, tuple, set)):
            filters = [filters]
        record = (filters, handler)
        if index is None:
            self.handlers.append(record)
        else:
            self.handlers.insert(index, record)

    def unregister(self, handler):
        """
        Remove handler

        :param handler: callback
        :return:
        """
        for handler_with_filters in self.handlers:
            _, registered = handler_with_filters
            if handler is registered:
                self.handlers.remove(handler_with_filters)
                return True
        raise ValueError('This handler is not registered!')

    async def notify(self, *args, **kwargs):
        """
        Notify handlers

        :param args:
        :param kwargs:
        :return:
        """
        results = []

        for filters, handler in self.handlers:
            if await check_filters(filters, args, kwargs):
                try:
                    response = await handler(*args, **kwargs)
                    if results is not None:
                        results.append(response)
                    if self.once:
                        break
                except SkipHandler:
                    continue
                except CancelHandler:
                    break

        return results
