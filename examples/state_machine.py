import asyncio
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.state import StateMachine

API_TOKEN = 'BOT TOKEN HERE'
API_TOKEN = '380294876:AAFbdYYgq1hBi9hQDcxD3bj8QCNnVec5aHk'

logging.basicConfig(level=logging.DEBUG)

loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)

users = {}


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Hi there! What's your name?")
    state.set_state(message.chat.id, message.from_user.id, "name")


async def process_name(message, controller):
    users[message.from_user.id] = {"name": message.text}

    await message.reply("How old are you?")

    controller.set('age')


async def process_age(message, controller):
    if not message.text.isdigit():
        return await message.reply("Age should be a number.\nHow old are you?")

    users[message.from_user.id].update({"age": int(message.text)})

    markup = types.ReplyKeyboardMarkup()
    markup.add("Male", "Female")
    markup.add("Other")
    await message.reply("What is your gender?", reply_markup=markup)
    controller.set("sex")


async def process_sex(message, controller):
    if message.text not in ["Male", "Female", "Other"]:
        return await message.reply("Bad gender name. Choose you gender from keyboard.")

    users[message.from_user.id].update({"sex": message.text})
    controller.clear()

    user = users[message.from_user.id]

    markup = types.ReplyKeyboardRemove()
    await bot.send_message(message.chat.id,
                           f"Hi!\nNice to meet you, {user['name']}.\nAge: {user['age']}\nSex: {user['sex']}",
                           reply_markup=markup)


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
