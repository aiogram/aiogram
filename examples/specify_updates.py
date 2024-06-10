import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import LEAVE_TRANSITION, ChatMemberUpdatedFilter, CommandStart
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.markdown import hbold, hcode

TOKEN = getenv("BOT_TOKEN")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """

    await message.answer(
        f"Hello, {hbold(message.from_user.full_name)}!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Tap me, bro", callback_data="*")]]
        ),
    )


@router.chat_member()
async def chat_member_update(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    await bot.send_message(
        chat_member.chat.id,
        f"Member {hcode(chat_member.from_user.id)} was changed "
        + f"from {chat_member.old_chat_member.status} to {chat_member.new_chat_member.status}",
    )


# this router will use only callback_query updates
sub_router = Router()


@sub_router.callback_query()
async def callback_tap_me(callback_query: CallbackQuery) -> None:
    await callback_query.answer("Yeah good, now I'm fine")


# this router will use only edited_message updates
sub_sub_router = Router()


@sub_sub_router.edited_message()
async def edited_message_handler(edited_message: Message) -> None:
    await edited_message.reply("Message was edited, Big Brother watches you")


# this router will use only my_chat_member updates
deep_dark_router = Router()


@deep_dark_router.my_chat_member(~ChatMemberUpdatedFilter(~LEAVE_TRANSITION))
async def my_chat_member_change(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    await bot.send_message(
        chat_member.chat.id,
        f"This Bot`s status was changed from {hbold(chat_member.old_chat_member.status)} "
        f"to {hbold(chat_member.new_chat_member.status)}",
    )


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    sub_router.include_router(deep_dark_router)
    router.include_routers(sub_router, sub_sub_router)
    dp.include_router(router)

    # Start event dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
