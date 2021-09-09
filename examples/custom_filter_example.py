from typing import Union
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

    def __init__(self):
        super(UserMiddleware, self).__init__()

    async def pre_process(
        self,
        update: Union[types.Message, types.CallbackQuery],
        data: dict,
    ):
        if update.from_user.id not in fake_db:
            fake_db[update.from_user.id] = {"ban": False}

        data["user_in_db"] = fake_db[update.from_user.id]


class BanUserFilter(BoundFilter):
    """
    Check if user banned in bot db
    """

    key = "banned"

    def __init__(self, banned: bool):
        if banned is False:
            raise ValueError("filter banned cannot be False")

    async def check(self, obj: Union[types.Message, types.CallbackQuery]):
        data = ctx_data.get()
        user_in_db = data["user_in_db"]

        return not user_in_db["ban"]


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


#  Setup middleware
dp.middleware.setup(UserMiddleware())

#  Binding filters
dp.filters_factory.bind(
    BanUserFilter,
    event_handlers=[dp.message_handlers, dp.callback_query_handlers],
)
dp.filters_factory.bind(
    IsEvenIdFilter,
    event_handlers=[dp.message_handlers, dp.callback_query_handlers],
)


@dp.message_handler(banned=True)
async def handler_start1(message: types.Message):
    await message.answer("Congratulations, you are banned!")


@dp.message_handler(commands="start", is_even=True)
async def handler_start2(message: types.Message, is_even: bool):
    if is_even:
        await message.answer("Congratulations, you id is even!")
    else:
        await message.answer("Congratulations, your id is not even")


if __name__ == "__main__":
    allowed_updates = types.AllowedUpdates.MESSAGE | types.AllowedUpdates.CALLBACK_QUERY
    executor.start_polling(dp, allowed_updates=allowed_updates)
