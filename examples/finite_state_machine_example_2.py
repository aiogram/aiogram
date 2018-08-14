"""
This example is equals with 'finite_state_machine_example.py' but with FSM Middleware

Note that FSM Middleware implements the more simple methods for working with storage.

With that middleware all data from storage will be loaded before event will be processed
and data will be stored after processing the event.
"""
import asyncio

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.fsm import FSMMiddleware, FSMSStorageProxy
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

API_TOKEN = 'BOT TOKEN HERE'

loop = asyncio.get_event_loop()

bot = Bot(token=API_TOKEN, loop=loop)

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(FSMMiddleware())


# States
class Form(StatesGroup):
    name = State()  # Will be represented in storage as 'Form:name'
    age = State()  # Will be represented in storage as 'Form:age'
    gender = State()  # Will be represented in storage as 'Form:gender'


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Form.first()

    await message.reply("Hi there! What's your name?")


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands=['cancel'])
@dp.message_handler(lambda message: message.text.lower() == 'cancel', state='*')
async def cancel_handler(message: types.Message, state_data: FSMSStorageProxy):
    """
    Allow user to cancel any action
    """
    if state_data.state is None:
        return

    # Cancel state and inform user about it
    del state_data.state
    # And remove keyboard (just in case)
    await message.reply('Canceled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state_data: FSMSStorageProxy):
    """
    Process user name
    """
    state_data.state = Form.age
    state_data['name'] = message.text

    await message.reply("How old are you?")


# Check age. Age gotta be digit
@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
async def failed_process_age(message: types.Message):
    """
    If age is invalid
    """
    return await message.reply("Age gotta be a number.\nHow old are you? (digits only)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state_data: FSMSStorageProxy):
    # Update state and data
    state_data.state = Form.gender
    state_data['age'] = int(message.text)

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Male", "Female")
    markup.add("Other")

    await message.reply("What is your gender?", reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["Male", "Female", "Other"], state=Form.gender)
async def failed_process_gender(message: types.Message):
    """
    In this example gender has to be one of: Male, Female, Other.
    """
    return await message.reply("Bad gender name. Choose you gender from keyboard.")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state_data: FSMSStorageProxy):
    state_data['gender'] = message.text

    # Remove keyboard
    markup = types.ReplyKeyboardRemove()

    # And send message
    await bot.send_message(message.chat.id, md.text(
        md.text('Hi! Nice to meet you,', md.bold(state_data['name'])),
        md.text('Age:', state_data['age']),
        md.text('Gender:', state_data['gender']),
        sep='\n'), reply_markup=markup, parse_mode=types.ParseMode.MARKDOWN)

    # Finish conversation
    # WARNING! This method will destroy all data in storage for current user!
    state_data.clear()


if __name__ == '__main__':
    executor.start_polling(dp, loop=loop, skip_updates=True)
