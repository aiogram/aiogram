"""
Internalize your bot

Step 1: extract texts
    # pybabel extract i18n_example.py -o locales/mybot.pot
Step 2: create *.po files. For e.g. create en, ru, uk locales.
    # echo {en,ru,uk} | xargs -n1 pybabel init -i locales/mybot.pot -d locales -D mybot -l
Step 3: translate texts
Step 4: compile translations
    # pybabel compile -d locales -D mybot

Step 5: When you change the code of your bot you need to update po & mo files.
    Step 5.1: regenerate pot file:
        command from step 1
    Step 5.2: update po files
        # pybabel update -d locales -D mybot -i locales/mybot.pot
    Step 5.3: update your translations
    Step 5.4: compile mo files
        command from step 4
"""

from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.i18n import I18nMiddleware

TOKEN = 'BOT TOKEN HERE'
I18N_DOMAIN = 'mybot'

BASE_DIR = Path(__file__).parent
LOCALES_DIR = BASE_DIR / 'locales'

bot = Bot(TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

# Setup i18n middleware
i18n = I18nMiddleware(I18N_DOMAIN, LOCALES_DIR)
dp.middleware.setup(i18n)

# Alias for gettext method
_ = i18n.gettext


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # Simply use `_('message')` instead of `'message'` and never use f-strings for translatable texts.
    await message.reply(_('Hello, <b>{user}</b>!').format(user=message.from_user.full_name))


@dp.message_handler(commands=['lang'])
async def cmd_lang(message: types.Message, locale):
    await message.reply(_('Your current language: <i>{language}</i>').format(language=locale))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
