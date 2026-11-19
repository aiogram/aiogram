Fixed the bot token appearing in network errors.
:class:`aiogram.exceptions.TelegramNetworkError` and the :code:`aiohttp` errors raised by :code:`Bot.download_file()` / :code:`Bot.download()` now show the token as :code:`<bot id>:***` in their message and traceback, and keep their type, so existing :code:`except` clauses still catch them.
The original exception is available as :code:`.original` and may contain the token.
Reported by the Anthropic OSS Scanner (ANT-2026-4GL80S7S).
