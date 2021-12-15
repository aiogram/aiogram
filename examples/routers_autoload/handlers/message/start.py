from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(commands=["start"])
async def process_message(m: Message):
    await m.answer("Hi!")
