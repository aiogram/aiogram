from aiogram import Router
from aiogram.types import Message

# add index -1 for this router to be registered the latest of all found in find_all_routers
router = Router(index=-1)


@router.message()
async def process_message(m: Message):
    await m.copy_to(chat_id=m.chat.id)
