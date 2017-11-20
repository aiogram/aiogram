import asyncio

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.utils.markdown import text, bold

API_TOKEN = 'BOT TOKEN HERE'

loop = asyncio.get_event_loop()

bot = Bot(token=API_TOKEN, loop=loop)

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# States
AGE = 'process_age'
NAME = 'process_name'
GENDER = 'process_gender'


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    """
    Entry point to conversation
    """
    # Get current state
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    # Update user state
    await state.set_state(NAME)

    await message.reply("Hi there! What's your name?")


# You can use state '*' if you need to handle all states.
@dp.message_handler(state='*', commands=['cancel'])
@dp.message_handler(state='*', func=lambda message: message.text.lower() == 'cancel')
async def cancel_handler(message: types.Message):
    """
    Allow to cancel any action
    """
    with dp.current_state(chat=message.chat.id, user=message.from_user.id) as state:
        # Ignore command if user is not in any (defined) state
        if await state.get_state() is None:
            return

        # Otherwise cancel state and inform user about that.
        # And just in case remove keyboard.
        await state.reset_state(with_data=True)
        await message.reply('Canceled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=NAME)
async def process_name(message: types.Message):
    """
    Process user name
    """
    # Save name to storage and go to next step
    # You can use context manager
    with dp.current_state(chat=message.chat.id, user=message.from_user.id) as state:
        await state.update_data(name=message.text)
        await state.set_state(AGE)

    await message.reply("How old are you?")


# Check age. Age must be is digit
@dp.message_handler(state=AGE, func=lambda message: not message.text.isdigit())
async def failed_process_age(message: types.Message):
    """
    If age is in invalid format
    """
    return await message.reply("Age should be a number.\nHow old are you?")


@dp.message_handler(state=AGE, func=lambda message: message.text.isdigit())
async def process_age(message: types.Message):
    # Update state and data
    with dp.current_state(chat=message.chat.id, user=message.from_user.id) as state:
        await state.set_state(GENDER)
        await state.update_data(age=int(message.text))

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Male", "Female")
    markup.add("Other")

    await message.reply("What is your gender?", reply_markup=markup)


@dp.message_handler(state=GENDER, func=lambda message: message.text not in ["Male", "Female", "Other"])
async def failed_process_sex(message: types.Message):
    """
    Sex must be always (in this example) is one of: Male, Female, Other.
    """
    return await message.reply("Bad gender name. Choose you gender from keyboard.")


@dp.message_handler(state=GENDER)
async def process_sex(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)

    data = await state.get_data()
    data['sex'] = message.text

    # Remove keyboard
    markup = types.ReplyKeyboardRemove()

    # And send message
    await bot.send_message(message.chat.id, text(
        text('Hi! Nice to meet you,', bold(data['name'])),
        text('Age:', data['age']),
        text('Sex:', data['sex']),
        sep='\n'), reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

    # Finish conversation
    # WARNING! This method will destroy all data in storage for current user!
    await state.finish()


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, loop=loop, skip_updates=True, on_shutdown=shutdown)
