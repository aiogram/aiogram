from aiogram import Bot, Dispatcher, types
import logging
import asyncio


API_TOKEN = "<TOKEN>"
logging.basicConfig(level=logging.INFO)

class AsyncioBot:

    # Initialize bot and dispatcher
    def __init__(self) -> None:
        self.bot = Bot(token=API_TOKEN)
        self.dp = Dispatcher(self.bot)

        self.dp.register_message_handler(self.on_message)

    async def on_message(self, message: types.Message):
        print(message.get_command())
        await message.answer(f"Asnwer: {message.text}")

    async def run(self):
        asyncio.create_task(self.dp.start_polling())  

if __name__ == '__main__':
    bot = AsyncioBot()
    loop = asyncio.get_event_loop()
    loop.create_task(bot.run())

    loop.run_forever()
    
