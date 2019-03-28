import inspect
from contextvars import ContextVar

ctx_data = ContextVar('ctx_handler_data')
current_handler = ContextVar('current_handler')


class SkipHandler(Exception):
    pass


class CancelHandler(Exception):
    pass


def _get_spec(func: callable):
    while hasattr(func, '__wrapped__'):  # Try to resolve decorated callbacks
        func = func.__wrapped__

    spec = inspect.getfullargspec(func)
    return spec, func


def _check_spec(spec, kwargs: dict):
    if spec.varkw:
        return kwargs

    return {k: v for k, v in kwargs.items() if k in spec.args}


class Handler:
    def __init__(self, dispatcher, once=True, middleware_key=None):
        self.dispatcher = dispatcher
        self.once = once

        self.handlers = []
        self.specs = {}
        self.middleware_key = middleware_key

    def register(self, handler, filters=None, index=None):
        """
        Register callback

        Filters can be awaitable or not.

        :param handler: coroutine
        :param filters: list of filters
        :param index: you can reorder handlers
        """
        spec, handler = _get_spec(handler)
        self.specs[handler] = spec

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
                self.specs.pop(handler, None)
                self.handlers.remove(handler_with_filters)
                return True
        raise ValueError('This handler is not registered!')

    async def notify(self, *args):
        """
        Notify handlers

        :param args:
        :return:
        """
        from .filters import check_filters, FilterNotPassed

        results = []

        data = {}
        ctx_data.set(data)

        if self.middleware_key:
            try:
                await self.dispatcher.middleware.trigger(f"pre_process_{self.middleware_key}", args + (data,))
            except CancelHandler:  # Allow to cancel current event
                return results

        try:
            for filters, handler in self.handlers:
                try:
                    data.update(await check_filters(self.dispatcher, filters, args))
                except FilterNotPassed:
                    continue
                else:
                    ctx_token = current_handler.set(handler)
                    try:
                        if self.middleware_key:
                            await self.dispatcher.middleware.trigger(f"process_{self.middleware_key}", args + (data,))
                        partial_data = _check_spec(self.specs[handler], data)
                        response = await handler(*args, **partial_data)
                        if response is not None:
                            results.append(response)
                        if self.once:
                            break
                    except SkipHandler:
                        continue
                    except CancelHandler:
                        break
                    finally:
                        current_handler.reset(ctx_token)
        finally:
            if self.middleware_key:
                await self.dispatcher.middleware.trigger(f"post_process_{self.middleware_key}",
                                                         args + (results, data,))

        return results
