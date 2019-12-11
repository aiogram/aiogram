from typing import Any

from aiogram import Router
from aiogram.api.methods import SendMessage
from aiogram.dispatcher.handler.message import MessageHandler

router = Router()


@router.message_handler(commands=["test"])
class MyHandler(MessageHandler):
    async def handle(self) -> Any:
        return SendMessage(chat_id=self.chat.id, text="<b>PASS</b>")
