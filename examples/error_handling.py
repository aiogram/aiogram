import asyncio
import html
import logging
from os import getenv

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import (
    Command,
    CommandObject,
    ExceptionMessageFilter,
    ExceptionTypeFilter,
)
from aiogram.types import ErrorEvent

TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()

logger = logging.getLogger(__name__)


class InvalidAge(Exception):
    pass


class InvalidName(Exception):
    def __init__(self, message: str):
        super().__init__(message)


@dp.errors(ExceptionTypeFilter(InvalidAge))
async def handle_invalid_age_exception(event: ErrorEvent, bot: Bot) -> None:
    """
    This handler receives only error events with `InvalidAge` exception type.
    """
    # To get the original event that caused the exception you can use `event.update` property.
    # In this case it will be `Message` object.
    # To get the exception itself you can use `event.exception` property.
    # In this case we filter errors, so we can be sure `event.exception` is an `InvalidAge` object.
    assert isinstance(event.exception, InvalidAge)
    logger.error("Error caught: %r while processing %r", event.exception, event.update)

    assert event.update.message is not None
    chat_id = event.update.message.chat.id

    # Bot instance is passed to the handler as a keyword argument.
    # We can use `bot.send_message` method to send a message to the user, logging the error.
    text = f"Error caught: {html.escape(repr(event.exception))}"
    await bot.send_message(chat_id=chat_id, text=text)


@dp.errors(ExceptionMessageFilter("Invalid"))
async def handle_invalid_exceptions(event: ErrorEvent) -> None:
    """
    This handler receives error events with "Invalid" message in them.
    """
    # Because we specified `ExceptionTypeFilter` with `InvalidAge` exception type earlier,
    # this handler will receive error events with any exception type except `InvalidAge` and
    # only if the exception message contains "Invalid" substring.
    logger.error("Error `Invalid` caught: %r while processing %r", event.exception, event.update)


@dp.message(Command("age"))
async def handle_set_age(message: types.Message, command: CommandObject) -> None:
    """
    This handler receives only messages with `/age` command.

    If the user sends a message with `/age` command, but the age is invalid,
    the `InvalidAge` exception will be raised and the `handle_invalid_age_exception`
    handler will be called.
    """
    # To get the command object you can use `command` keyword argument with `CommandObject` type.
    # To get the command arguments you can use `command.args` property.
    age = command.args
    if not age:
        raise InvalidAge("No age provided. Please provide your age as a command argument.")

    # If the age is invalid, raise an exception.
    if not age.isdigit():
        raise InvalidAge("Age should be a number")

    # If the age is valid, send a message to the user.
    age = int(age)
    await message.reply(text=f"Your age is {age}")


@dp.message(Command("name"))
async def handle_set_name(message: types.Message, command: CommandObject) -> None:
    """
    This handler receives only messages with `/name` command.
    """
    # To get the command object you can use `command` keyword argument with `CommandObject` type.
    # To get the command arguments you can use `command.args` property.
    name = command.args
    if not name:
        raise InvalidName("Invalid name. Please provide your name as a command argument.")

    # If the name is valid, send a message to the user.
    await message.reply(text=f"Your name is {name}")


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
