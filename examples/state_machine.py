import asyncio
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.state import StateMachine

API_TOKEN = 'BOT TOKEN HERE'

logging.basicConfig(level=logging.DEBUG)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Hi there! What's your name?")
    state.set_state(message.chat.id, message.from_user.id, "name")


async def process_name(message, controller):
    controller["name"] = message.text

    await message.reply("How old are you?")

    controller.set_state('age')


async def process_age(message, controller):
    if not message.text.isdigit():
        return await message.reply("Age should be a number.\nHow old are you?")

    controller["age"] = int(message.text)

    markup = types.ReplyKeyboardMarkup()
    markup.add("Male", "Female")
    markup.add("Other")
    await message.reply("What is your gender?", reply_markup=markup)

    controller.set_state("sex")


async def process_sex(message, controller):
    if message.text not in ["Male", "Female", "Other"]:
        return await message.reply("Bad gender name. Choose you gender from keyboard.")

    controller["sex"] = message.text

    markup = types.ReplyKeyboardRemove()
    await bot.send_message(message.chat.id,
                           f"Hi!\n"
                           f"Nice to meet you, {controller['name']}.\n"
                           f"Age: {controller['age']}\n"
                           f"Sex: {controller['sex']}",
                           reply_markup=markup)
    controller.clear()


state = StateMachine(dp, {
    "name": process_name,
    "age": process_age,
    "sex": process_sex
})

if __name__ == '__main__':
    try:
        loop.run_until_complete(dp.start_pooling())
    except KeyboardInterrupt:
        loop.stop()
