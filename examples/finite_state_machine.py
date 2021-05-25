import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, F
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import hbold
from aiogram.utils.markup import KeyboardConstructor

GENDERS = ["Male", "Female", "Helicopter", "Other"]

dp = Dispatcher()


# States
class Form(StatesGroup):
    name = State()  # Will be represented in storage as 'Form:name'
    age = State()  # Will be represented in storage as 'Form:age'
    gender = State()  # Will be represented in storage as 'Form:gender'


@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message, state: FSMContext):
    """
    Conversation's entry point
    """
    # Set state
    await state.set_state(Form.name)
    await message.answer("Hi there! What's your name?")


@dp.message(Command(commands=["cancel"]))
@dp.message(F.text.lower() == "cancel")
async def cancel_handler(message: Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    # Cancel state and inform user about it
    await state.clear()
    # And remove keyboard (just in case)
    await message.answer("Cancelled.", reply_markup=ReplyKeyboardRemove())


@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    """
    Process user name
    """
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("How old are you?")


# Check age. Age gotta be digit
@dp.message(Form.age, ~F.text.isdigit())
async def process_age_invalid(message: Message):
    """
    If age is invalid
    """
    return await message.answer("Age gotta be a number.\nHow old are you? (digits only)")


@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    # Update state and data
    await state.set_state(Form.gender)
    await state.update_data(age=int(message.text))

    # Configure ReplyKeyboardMarkup
    constructor = KeyboardConstructor(KeyboardButton)
    constructor.add(*(KeyboardButton(text=text) for text in GENDERS)).adjust(2)
    markup = ReplyKeyboardMarkup(
        resize_keyboard=True, selective=True, keyboard=constructor.export()
    )
    await message.reply("What is your gender?", reply_markup=markup)


@dp.message(Form.gender)
async def process_gender(message: Message, state: FSMContext):
    data = await state.update_data(gender=message.text)
    await state.clear()

    # And send message
    await message.answer(
        (
            f'Hi, nice to meet you, {hbold(data["name"])}\n'
            f'Age: {hbold(data["age"])}\n'
            f'Gender: {hbold(data["gender"])}\n'
        ),
        reply_markup=ReplyKeyboardRemove(),
    )


async def main():
    bot = Bot(token=getenv("TELEGRAM_TOKEN"), parse_mode="HTML")

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
