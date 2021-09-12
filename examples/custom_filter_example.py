from typing import Any, Union
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

API_TOKEN = "BOT_TOKEN_HERE"


fake_db = {
    0000000000: {"ban": True},
    1111111111: {"ban": False},
    2222222222: {"ban": True},
    3333333333: {"ban": False},
}


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


class UserMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]

    async def pre_process(
        self,
        obj: Union[types.Message, types.CallbackQuery],
        data: dict,
    ):
        user = obj.from_user
        if user.id not in fake_db:
            fake_db[user.id] = {"ban": False}

        data["user_in_db"] = fake_db[user.id]


class BanUserFilter(BoundFilter):
    """
    Check if user banned in bot db
    """

    key = "banned"

    def __init__(self, banned: bool):
        self.banned = banned

    async def check(self, obj: Any):
        data: dict = ctx_data.get()
        user_in_db = data.get("user_in_db", None)
        if user_in_db:
            return self.banned == user_in_db["ban"]
        return False  # If the user is not in the database, then he cannot be banned


class IsEvenIdFilter(BoundFilter):
    """
    Check if user.id is even
    """

    key = "is_even"

    def __init__(self, is_even: bool):
        if is_even is False:
            raise ValueError("filter is_even cannot be False")

    async def check(self, obj: Union[types.Message, types.CallbackQuery]):
        user_id = obj.from_user.id
        return {"is_even": bool(user_id % 2 == 0)}


class DatabaseIsNotEmptyFilter(BoundFilter):
    """
    Check if the database contains the required number of records
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
        return len(fake_db) >= self.data_in_db


#  Setup middleware
dp.middleware.setup(UserMiddleware())

#  Binding filters
dp.filters_factory.bind(
    BanUserFilter,
    exclude_event_handlers=[dp.channel_post_handlers, dp.edited_channel_post_handlers],
)
dp.filters_factory.bind(
    IsEvenIdFilter,
    event_handlers=[dp.message_handlers, dp.callback_query_handlers],
)
dp.filters_factory.bind(DatabaseIsNotEmptyFilter)


@dp.message_handler(banned=True)
async def handler_start1(message: types.Message):
    await message.answer("Congratulations, you are banned!")


@dp.message_handler(data_in_db=6)
async def handler_start2(message: types.Message):
    await message.answer("There are too many records in the database!")


@dp.message_handler(is_even=True)
async def handler_start3(message: types.Message, is_even: bool):
    if is_even:
        await message.answer("Congratulations, your id is even!")
    else:
        await message.answer("Congratulations, your id is not even :(")


if __name__ == "__main__":
    allowed_updates = types.AllowedUpdates.MESSAGE | types.AllowedUpdates.CALLBACK_QUERY
    executor.start_polling(dp, allowed_updates=allowed_updates)
