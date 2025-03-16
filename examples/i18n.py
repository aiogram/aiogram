"""
Original docs link: https://docs.aiogram.dev/en/dev-3.x/utils/i18n.html
PROBLEM SOLUTION PROVIDED:
Aiogram handlers remember language on the start and there's no chance of changing it in handler's runtime.
So, here's a little hack in `change_language handler`

# Cheatsheet to create/update locales:
## Generating new:
1. `pybabel extract -k __ --input-dirs=. -o locales/messages.pot`
2. `pybabel init -i locales/messages.pot -d locales -D messages -l <en ru uk>`
3. Open `locales/{language}/LC_MESSAGES/messages.po` and Translate msgs
4. `pybabel compile -d locales -D messages`

## Updating:
1. `pybabel extract -k __ --input-dirs=. -o locales/messages.pot`
2. `pybabel update -d locales -D messages -i locales/messages.pot`
3. Open `locales/{language}/LC_MESSAGES/messages.po` and Translate msgs
4. `pybabel compile -d locales -D messages`

"""
import asyncio
from typing import Any

from aiogram import Bot, Dispatcher, Router
from aiogram import types
from aiogram.filters.command import Command, CommandStart
from aiogram.utils.i18n import gettext as _, I18n
from aiogram.utils.i18n.middleware import I18nMiddleware, SimpleI18nMiddleware


# class BotI18nMiddleware(I18nMiddleware):
#     async def get_locale(self, event: types.Update | Any, data: dict[str, Any]) -> str:
#         # here is your logic, ex. get language from redis DB.
#         return 'en'


bot = Bot(token="<Your token>")
router = Router()
dp = Dispatcher()
# NOTE: basic middleware is provided. You can customize your middleware, ex. BotI18nMiddleware
i18n_middleware = SimpleI18nMiddleware(
    I18n(
        path="locales",
        default_locale="en",
        domain="messages"
    )
)
dp.update.outer_middleware(i18n_middleware)


@router.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        _("Hello!. Write /language <new_lang>. Ex: /language ru")
    )


@router.message(Command("language"))
async def change_language(message: types.Message):
    """
    This function dynamically changes language inside of handler
    Handler input: /language <new_lang>. Ex: /language ru

    Aiogram saves language context on start, so we should change language in runtime
    """
    new_lang = message.text.split(maxsplit=1)[1]
    # change in runtime
    with i18n_middleware.i18n.context(), i18n_middleware.i18n.use_locale(new_lang):
        # all messages in this context will be translated to new_lang
        await message.answer(_('Language was changed to {lang}').format(lang=new_lang))


dp.include_router(router)


async def main():
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
