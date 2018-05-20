from .filters import check_filters
from ..utils import context


class SkipHandler(BaseException):
    pass


class CancelHandler(BaseException):
    pass


class Handler:
    def __init__(self, dispatcher, once=True, middleware_key=None):
        self.dispatcher = dispatcher
        self.once = once

        self.handlers = []
        self.middleware_key = middleware_key

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

    async def notify(self, *args):
        """
        Notify handlers

        :param args:
        :return:
        """
        results = []

        if self.middleware_key:
            try:
                await self.dispatcher.middleware.trigger(f"pre_process_{self.middleware_key}", args)
            except CancelHandler:  # Allow to cancel current event
                return results

        for filters, handler in self.handlers:
            if await check_filters(filters, args):
                try:
                    if self.middleware_key:
                        context.set_value('handler', handler)
                        await self.dispatcher.middleware.trigger(f"process_{self.middleware_key}", args)
                    response = await handler(*args)
                    if response is not None:
                        results.append(response)
                    if self.once:
                        break
                except SkipHandler:
                    continue
                except CancelHandler:
                    break
        if self.middleware_key:
            await self.dispatcher.middleware.trigger(f"post_process_{self.middleware_key}",
                                                     args + (results,))

        return results
