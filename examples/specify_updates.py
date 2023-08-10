import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode, UpdateType
from aiogram.filters import LEAVE_TRANSITION, ChatMemberUpdatedFilter, CommandStart
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

TOKEN = "6wo"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """

    await message.answer(
        f"Hello, <b>{message.from_user.full_name}!</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Tap me, bro", callback_data="*")]]
        ),
    )


@router.chat_member()
async def chat_member_update(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    await bot.send_message(
        chat_member.chat.id,
        "Member {chat_member.from_user.id} was changed "
        + f"from {chat_member.old_chat_member.status} to {chat_member.new_chat_member.status}",
    )


# this router will use only callback_query updates
sub_router = Router()


@sub_router.callback_query()
async def callback_tap_me(callback_query: CallbackQuery) -> None:
    await callback_query.answer("Yeah good, now i'm fine")


# this router will use only edited_message updates
sub_sub_router = Router()


@sub_sub_router.edited_message()
async def edited_message_handler(edited_message: Message) -> None:
    await edited_message.reply("Message was edited, Big Brother watches you")


# this router will use only my_chat_member updates
deep_dark_router = Router()


@deep_dark_router.my_chat_member(~ChatMemberUpdatedFilter(LEAVE_TRANSITION))
async def my_chat_member_change(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    await bot.send_message(
        chat_member.chat.id,
        "This Bot`s status was changed from "
        + f"{chat_member.old_chat_member.status} to {chat_member.new_chat_member.status}",
    )


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)

    dp = Dispatcher()
    dp.include_router(router)
    sub_router.include_router(deep_dark_router)
    router.include_router(sub_router)
    router.include_router(sub_sub_router)

    # Specify which updates should be handled by Dispatcher.
    # By default, all types, that used in handlers will be used.
    useful_updates = [
        UpdateType.MESSAGE,
        UpdateType.CALLBACK_QUERY,
        UpdateType.EDITED_MESSAGE,
        # UpdateType.MY_CHAT_MEMBER,  # Here we decided to skip the my_chat_member updates, even though it's used in our handlers. Uncomment this line to enable it.
    ]

    # Start event dispatching
    await dp.start_polling(bot, allowed_updates=useful_updates)

    # If you want to use all the update types registered in the dispatcher, you should not specify the `allowed_updates` parameter:
    # await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
