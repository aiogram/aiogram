from asyncio import Event

from .filters import check_filters, CancelFilter
from .. import types


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


class NextStepHandler:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.handlers = {}

    def register(self, message, otherwise=None, once=False, include_cancel=False, filters=None):
        identifier = gen_identifier(message.chat.id, message.chat.id)

        if identifier not in self.handlers:
            self.handlers[identifier] = {'event': Event(), 'filters': filters,
                                         'otherwise': otherwise, 'once': once,
                                         'include_cancel': include_cancel,
                                         'message': None}
            return True

        # In normal it's impossible.
        raise RuntimeError('Dialog already wait message.')
        # return False

    async def notify(self, message):
        identifier = gen_identifier(message.chat.id, message.chat.id)
        if identifier not in self.handlers:
            return False
        handler = self.handlers[identifier]

        include_cancel = handler['include_cancel']
        if include_cancel:
            filter_ = CancelFilter(include_cancel if isinstance(include_cancel, (list, set, tuple)) else None)
            if filter_.check(message):
                handler['event'].set()
                return True

        if handler['filters'] and not await check_filters(handler['filters'], [message], {}):
            otherwise = handler['otherwise']
            if otherwise:
                await otherwise(message)
            if handler['once']:
                handler['event'].set()
            return True

        handler['message'] = message
        handler['event'].set()
        return True

    async def wait(self, message) -> types.Message:
        identifier = gen_identifier(message.chat.id, message.chat.id)

        handler = self.handlers[identifier]
        event = handler.get('event')

        await event.wait()
        message = self.handlers[identifier]['message']
        self.reset(identifier)
        return message

    def reset(self, identifier):
        del self.handlers[identifier]


def gen_identifier(chat_id, from_user_id):
    return f"{chat_id}:{from_user_id}"
