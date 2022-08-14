import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

TOKEN = "6wo"
dp = Dispatcher()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dp.message(Command(commands=["start"]))
async def command_start_handler(message: Message) -> None:
    """
    This handler receive messages with `/start` command
    """

    await message.answer(
        f"Hello, <b>{message.from_user.full_name}!</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Tap me, bro", callback_data="*")]]
        ),
    )


@dp.chat_member()
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
    await edited_message.reply("Message was edited, big brother watch you")


# this router will use only my_chat_member updates
deep_dark_router = Router()


@deep_dark_router.my_chat_member()
async def my_chat_member_change(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    await bot.send_message(
        chat_member.chat.id,
        "Member was changed from "
        + f"{chat_member.old_chat_member.status} to {chat_member.new_chat_member.status}",
    )


def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode="HTML")

    sub_router.include_router(deep_dark_router)

    dp.include_router(sub_router)
    dp.include_router(sub_sub_router)

    useful_updates = dp.resolve_used_update_types()

    # And the run events dispatching
    dp.run_polling(bot, allowed_updates=useful_updates)


if __name__ == "__main__":
    main()
