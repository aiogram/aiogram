import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
TOKEN = 7537770028:AAEBMd-n9Nce8EjHy6c6sFKSucpYKXrBU08
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
tap_button = KeyboardButton('Тап!')
keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(tap_button)
/start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Привет! Нажимай на кнопку 'Тап!' чтобы тапать.", reply_markup=keyboard)

# Обработчик нажатия на кнопку 'Тап!'
@dp.message_handler(lambda message: message.text == 'Тап!')
async def handle_tap(message: types.Message):
    await message.answer("Ты тапнул!")

# Обработчик любых текстовых сообщений
@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def handle_text(message: types.Message):
    await message.answer("Просто тапай!")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
