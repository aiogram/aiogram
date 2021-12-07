from typing import List, Union
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import BoundFilter

API_TOKEN = "BOT_TOKEN_HERE"


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
    Check if the user is a bot admin
    """

    key = "global_admin"

    def __init__(self, global_admin: bool):
        self.global_admin = global_admin

    async def check(self, obj: Union[types.Message, types.CallbackQuery]):
        user = obj.from_user
        if user.id in ADMIN_IDS:
            return self.global_admin is True
        return self.global_admin is False


class MimeTypeFilter(BoundFilter):
    """
    Check document mime_type
    """

    key = "mime_type"

    def __init__(self, mime_type: Union[str, List[str]]):
        if isinstance(mime_type, str):
            self.mime_types = [mime_type]

        elif isinstance(mime_type, list):
            self.mime_types = mime_type

        else:
            raise ValueError(
                f"filter mime_types must be a str or list of str, not {type(mime_type).__name__}"
            )

    async def check(self, obj: types.Message):
        if not obj.document:
            return False

        if obj.document.mime_type in self.mime_types:
            return True

        return False


class LettersInMessageFilter(BoundFilter):
    """
    Checking for the number of characters in a message/callback_data
    """

    key = "letters"

    def __init__(self, letters: int):
        if isinstance(letters, int):
            self.letters = letters
        else:
            raise ValueError(
                f"filter letters must be a int, not {type(letters).__name__}"
            )

    async def check(self, obj: Union[types.Message, types.CallbackQuery]):
        data = obj.text or obj.data
        if data:
            letters_in_message = len(data)
            if letters_in_message > self.letters:
                return False
            return {"letters": letters_in_message}
        return False


#  Binding filters
dp.filters_factory.bind(
    GlobalAdminFilter,
    exclude_event_handlers=[dp.channel_post_handlers, dp.edited_channel_post_handlers],
)
dp.filters_factory.bind(MimeTypeFilter, event_handlers=[dp.message_handlers])
dp.filters_factory.bind(LettersInMessageFilter)


@dp.message_handler(letters=5)
async def handle_letters_in_message(message: types.Message, letters: int):
    await message.answer(f"Message too short!\nYou sent only {letters} letters")


@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, mime_type="text/plain")
async def handle_txt_documents(message: types.Message):
    await message.answer("This is a text file!")


@dp.message_handler(
    content_types=types.ContentTypes.DOCUMENT, mime_type=["image/jpeg", "image/png"]
)
async def handle_photo_documents(message: types.Message):
    await message.answer("This is a photo file!")


@dp.message_handler(global_admin=True)
async def handle_admins(message: types.Message):
    await message.answer("Congratulations, you are global admin!")


if __name__ == "__main__":
    allowed_updates = types.AllowedUpdates.MESSAGE | types.AllowedUpdates.CALLBACK_QUERY
    executor.start_polling(dp, allowed_updates=allowed_updates, skip_updates=True)
