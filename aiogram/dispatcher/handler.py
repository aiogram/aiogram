from asyncio import Event

from aiogram import types
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


class NextStepHandler:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.handlers = {}

    def register(self, message, otherwise=None, once=False, filters=None):
        chat_id = message.chat.id
        if chat_id not in self.handlers:
            self.handlers[chat_id] = {'event': Event(), 'filters': filters,
                                      'otherwise': otherwise, 'once': once}
            return True
        return False

    async def notify(self, message):
        chat_id = message.chat.id
        if chat_id not in self.handlers:
            return False
        handler = self.handlers[chat_id]
        if handler['filters'] and not await check_filters(handler['filters'], [message], {}):
            otherwise = handler['otherwise']
            if otherwise:
                await otherwise(message)
            if not handler['once']:
                return False
        handler['message'] = message
        handler['event'].set()
        return True

    async def wait(self, message) -> types.Message:
        chat_id = message.chat.id
        handler = self.handlers[chat_id]
        event = handler.get('event')

        await event.wait()
        message = self.handlers[chat_id]['message']
        self.reset(chat_id)
        return message

    def reset(self, identifier):
        del self.handlers[identifier]
