from typing import Any, Union
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import BoundFilter

API_TOKEN = "BOT_TOKEN_HERE"


LIMIT_DATABASE_RECORDS = 6


ADMIN_IDS = [
    000000000,
    111111111,
    222222222,
    333333333,
    444444444,
]


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


class GlobalAdminFilter(BoundFilter):
    """
    Check if user bot admin
    """

    key = "global_admin"

    def __init__(self, global_admin: bool):
        self.global_admin = global_admin

    async def check(self, obj: Union[types.Message, types.CallbackQuery]):
        user = obj.from_user
        if user.id in ADMIN_IDS:
            return self.global_admin is True
        return self.global_admin is False


class IsEvenIdFilter(BoundFilter):
    """
    Check if user.id is even
    """

    key = "is_even"

    def __init__(self, is_even: int):
        if isinstance(is_even, int):
            self.is_even = is_even
        else:
            raise ValueError(
                f"filter is_even must be a int, not {type(is_even).__name__}"
            )

    async def check(self, obj: Union[types.Message, types.CallbackQuery]):
        user_id = obj.from_user.id
        return bool(user_id % self.is_even == 0)


class DatabaseIsNotEmptyFilter(BoundFilter):
    """
    Check if the bot admins users contains the required number of records
    """

    key = "data_in_db"

    def __init__(self, data_in_db: int):
        if isinstance(data_in_db, int):
            self.data_in_db = data_in_db
        else:
            raise ValueError(
                f"filter data_in_db must be a int, not {type(data_in_db).__name__}"
            )

    async def check(self, obj: Any):
        return {"data_in_db": self.data_in_db - len(ADMIN_IDS)}


#  Binding filters
dp.filters_factory.bind(
    GlobalAdminFilter,
    exclude_event_handlers=[dp.channel_post_handlers, dp.edited_channel_post_handlers],
)
dp.filters_factory.bind(
    IsEvenIdFilter,
    event_handlers=[dp.message_handlers, dp.callback_query_handlers],
)
dp.filters_factory.bind(DatabaseIsNotEmptyFilter)


@dp.message_handler(commands="is_even", is_even=2)
async def handle_even_id(message: types.Message):
    await message.answer("Congratulations, your id is even!")


@dp.message_handler(commands="is_even", is_even=1)
async def handle_not_even_id(message: types.Message):
    await message.answer("Sorry, but your id... is not even....")


@dp.message_handler(data_in_db=LIMIT_DATABASE_RECORDS)
async def handle_full_database(message: types.Message, data_in_db: int):
    await message.answer(f"Too many records in the database.\nLimit {LIMIT_DATABASE_RECORDS}, current {data_in_db}")


@dp.message_handler(global_admin=True)
async def handle_admins(message: types.Message):
    await message.answer("Congratulations, you are global admin!")


if __name__ == "__main__":
    allowed_updates = types.AllowedUpdates.MESSAGE | types.AllowedUpdates.CALLBACK_QUERY
    executor.start_polling(dp, allowed_updates=allowed_updates, skip_updates=True)
