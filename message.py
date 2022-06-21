import asyncio
import secrets

from aiogram import Bot


async def main():
    bot = Bot(token="5115369270:AAFlipWd1qbhc7cIe0nRM-SyGLkTC_9Ulgg")
    index = 0
    while True:
        index += 1
        print(index)
        await bot.send_message(chat_id=879238251, text=secrets.token_urlsafe(24))
        await asyncio.sleep(.2)


asyncio.run(main())
