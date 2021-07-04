from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.dispatcher.router import Router
from aiogram.utils.handlers_in_use import get_handlers_in_use
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatMemberUpdated, CallbackQuery

TOKEN = "6wo"
dp = Dispatcher()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dp.message(commands={"start"})
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
        + f"from {chat_member.old_chat_member.is_chat_member} to {chat_member.new_chat_member.is_chat_member}",
    )


# this router will use only callback_query updates
sub_router = Router()


@sub_router.callback_query()
async def callback_tap_me(callback_query: CallbackQuery) -> None:
    await callback_query.answer("Yeah good, now i'm fine")


# this router will use only edited_message updates
sub_sub_router = Router()


@sub_sub_router.edited_message()
async def callback_tap_me(edited_message: Message) -> None:
    await edited_message.reply("Message was edited, big brother watch you")


# this router will use only my_chat_member updates
deep_dark_router = Router()


@deep_dark_router.my_chat_member()
async def my_chat_member_change(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    await bot.send_message(
        chat_member.chat.id,
        "Member was changed from "
        + f"{chat_member.old_chat_member.is_chat_member} to {chat_member.new_chat_member.is_chat_member}",
    )


def main() -> None:
    # Initialize Bot instance with an default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode="HTML")

    sub_router.include_router(deep_dark_router)

    dp.include_router(sub_router)
    dp.include_router(sub_sub_router)

    useful_updates = get_handlers_in_use(dp)

    # And the run events dispatching
    dp.run_polling(bot, allowed_updates=useful_updates)


if __name__ == "__main__":
    main()
