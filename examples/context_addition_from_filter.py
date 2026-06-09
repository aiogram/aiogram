from typing import Any

from aiogram import Router
from aiogram.filters import Filter
from aiogram.types import Message, User

router = Router(name=__name__)


class HelloFilter(Filter):
    def __init__(self, name: str | None = None) -> None:
        self.name = name

    async def __call__(
        self,
        message: Message,
        event_from_user: User,
        # Filters also can accept keyword parameters like in handlers
    ) -> bool | dict[str, Any]:
        if message.text.casefold() == "hello":
            # Returning a dictionary that will update the context data
            return {"name": event_from_user.mention_html(name=self.name)}
        return False


@router.message(HelloFilter())
async def my_handler(
    message: Message,
    name: str,  # Now we can accept "name" as named parameter
) -> Any:
    return message.answer(f"Hello, {name}!")
