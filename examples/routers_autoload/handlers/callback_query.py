from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query()
async def process_callback_query(q: CallbackQuery):
    await q.answer("Success!", show_alert=True)
