import logging
from typing import Union

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)

API_TOKEN = 'BOT_TOKEN_HERE'


bot = Bot(token=API_TOKEN)

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    name = State()  # Will be represented in storage as 'Form:name'
    age = State()  # Will be represented in storage as 'Form:age'
    gender = State()  # Will be represented in storage as 'Form:gender'


# You can use pre_set decorator to call decorated functions before state will be setted
@Form.name.pre_set
async def name_pre_set(context: FSMContext, old_state: str, new_state: str):
    logging.info('Calling before Form:name will be set')
    await bot.send_message(
        chat_id = context.chat,
        text = "What's your name?"
    )


# You can use post_set decorator to call decorated functions after state will be setted
@Form.age.post_set
async def age_post_set(context: FSMContext, old_state: str, new_state: str):
    logging.info('Calling after Form:age will be set')
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.row(types.InlineKeyboardButton('Back', callback_data='back'))

    await bot.send_message(
        chat_id = context.chat,
        text = "How old are you?",
        reply_markup = markup
    )


@Form.gender.pre_set
async def gender_pre_set(context: FSMContext, old_state: str, new_state: str):
    logging.info('Calling before gender:age will be set')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Male", "Female")
    markup.add("Other", "Back")

    await bot.send_message(
        chat_id = context.chat,
        text = "What is your gender?",
        reply_markup = markup
    )


# You can use pre_finish decorator to call decorated functions before state group will be finished
@Form.pre_finish
async def form_post_finish(context: FSMContext, old_state: str):
    async with context.proxy() as data:
        markup = types.ReplyKeyboardRemove()

        await bot.send_message(
            context.chat,
            md.text(
                md.text('Hi! Nice to meet you,', md.bold(data['name'])),
                md.text('Age:', md.code(data['age'])),
                md.text('Gender:', data['gender']),
                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )


# You can use state Form if you need to handle all states from Form group
@dp.message_handler(commands='back', state=Form)
@dp.message_handler(Text(equals='back', ignore_case=True), state=Form)
@dp.callback_query_handler(text='back', state=Form)
async def process_gender_invalid(message: Union[types.Message, types.CallbackQuery]):
    await Form.previous()


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    # You can set trigger to False to prevent pre_set and post_set signals
    await state.finish(trigger=False)
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    await message.reply("Hi there!")
    await Form.name.set()


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process user name and go to age
    """
    await state.update_data(name=message.text)
    await Form.next()


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
async def process_age_invalid(message: types.Message):
    """
    If age is not digit
    """
    return await message.reply("Age gotta be a number.\nHow old are you? (digits only)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    """
    Process user age and go to gender
    """
    await state.update_data(age=int(message.text))
    await Form.next()
    

@dp.message_handler(lambda message: message.text not in ["Male", "Female", "Other"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    """
    In this example gender has to be one of: Male, Female, Other.
    """
    return await message.reply("Bad gender name. Choose your gender from the keyboard.")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
