import asyncio
import os
from typing import Any, Dict, Union

from aiogram import Bot, types
from aiogram.api.types import Update
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.filters.base import BaseFilter
from aiogram.dispatcher.router import Router

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


class Text(BaseFilter):
    text: str

    async def __call__(self, obj: types.Message) -> Union[bool, Dict[str, Any]]:
        if obj.text == self.text:
            return {"text": self.text}


dp = Dispatcher()
router2 = Router()
router3 = Router()
dp.include_router(router2)
router2.include_router(router3)
dp.message_handler.bind_filter(Text)


@dp.message_handler(text="1")
async def message_handler_1(message: types.Message, bot: Bot):
    await bot.send_message(chat_id=message.from_user.id, text="PASS: 1")


@router2.message_handler(text="2")
async def message_handler_2(message: types.Message, bot: Bot, text: str):
    await bot.send_message(chat_id=message.from_user.id, text=f"PASS: {text}")


@router3.message_handler(text="3")
async def message_handler_3(message: types.Message, event_update: Update, bot: Bot):
    await bot.send_message(
        chat_id=message.from_user.id, text=event_update.json(skip_defaults=True, by_alias=True)
    )


async def main():
    async with Bot(TELEGRAM_TOKEN) as bot:
        await dp.polling(bot=bot)


if __name__ == "__main__":
    asyncio.run(main())
