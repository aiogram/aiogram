"""
Internationalize your bot

Step 1: extract texts
    # pybabel extract --input-dirs=. -o locales/mybot.pot

    Some useful options:
    - Extract texts with pluralization support
    # -k __:1,2
    - Add comments for translators, you can use another tag if you want (TR)
    # --add-comments=NOTE
    - Disable comments with string location in code
    # --no-location
    - Set project name
    # --project=MySuperBot
    - Set version
    # --version=2.2

Step 2: create *.po files. E.g. create en, ru, uk locales.
    # pybabel init -i locales/mybot.pot -d locales -D mybot -l en
    # pybabel init -i locales/mybot.pot -d locales -D mybot -l ru
    # pybabel init -i locales/mybot.pot -d locales -D mybot -l uk
    
Step 3: translate texts located in locales/{language}/LC_MESSAGES/mybot.po
    To open .po file you can use basic text editor or any PO editor, e.g. https://poedit.net/

Step 4: compile translations
    # pybabel compile -d locales -D mybot

Step 5: When you change the code of your bot you need to update po & mo files.
    Step 5.1: regenerate pot file:
        command from step 1
    Step 5.2: update po files
        # pybabel update -d locales -D mybot -i locales/mybot.pot
    Step 5.3: update your translations 
        location and tools you know from step 3
    Step 5.4: compile mo files
        command from step 4
"""

from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.i18n import I18nMiddleware

TOKEN = 'BOT_TOKEN_HERE'
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


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    # Simply use `_('message')` instead of `'message'` and never use f-strings for translatable texts.
    await message.reply(_('Hello, <b>{user}</b>!').format(user=message.from_user.full_name))


@dp.message_handler(commands='lang')
async def cmd_lang(message: types.Message, locale):
    # For setting custom lang you have to modify i18n middleware
    await message.reply(_('Your current language: <i>{language}</i>').format(language=locale))

# If you care about pluralization, here's small handler
# And also, there's and example of comments for translators. Most translation tools support them.

# Alias for gettext method, parser will understand double underscore as plural (aka ngettext)
__ = i18n.gettext


# some likes manager
LIKES_STORAGE = {'count': 0}


def get_likes() -> int:
    return LIKES_STORAGE['count']


def increase_likes() -> int:
    LIKES_STORAGE['count'] += 1
    return get_likes()


@dp.message_handler(commands='like')
async def cmd_like(message: types.Message, locale):
    likes = increase_likes()

    # NOTE: This is comment for a translator
    await message.reply(__('Aiogram has {number} like!', 'Aiogram has {number} likes!', likes).format(number=likes))

    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
