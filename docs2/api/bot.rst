###
Bot
###

Bot instance can be created from :code:`aiogram.Bot` (:code:`from aiogram import Bot`) and
you can't use API methods without instance of bot with configured token.

This class has aliases for all API methods and named in :code:`lower_camel_case`.

For example :code:`sendMessage` named :code:`send_message` and has the same specification with all class-based methods.

.. autoclass:: aiogram.api.client.bot.Bot
    :members:
    :show-inheritance:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True