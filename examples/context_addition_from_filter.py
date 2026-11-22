from typing import Any

from aiogram import Router
from aiogram.dispatcher.middlewares.user_context import EventContext
from aiogram.filters import Filter
from aiogram.types import Message

router = Router(name=__name__)


class HelloFilter(Filter):
    def __init__(self, name: str | None = None) -> None:
        self.name = name

    async def __call__(
        self,
        message: Message,
        event_context: EventContext,
        # Filters also can accept keyword parameters like in handlers
    ) -> bool | dict[str, Any]:
        if message.text and message.text.casefold() == "hello" and event_context.user:
            # Returning a dictionary that will update the context data
            return {"name": event_context.user.mention_html(name=self.name)}
        return False


@router.message(HelloFilter())
async def my_handler(
    message: Message,
    name: str,  # Now we can accept "name" as named parameter
) -> Any:
    return message.answer(f"Hello, {name}!")
