###
Bot
###

Bot instance can be created from :code:`aiogram.Bot` (:code:`from aiogram import Bot`) and
you can't use methods without instance of bot with configured token.

This class has aliases for all methods and named in :code:`lower_camel_case`.

For example :code:`sendMessage` named :code:`send_message` and has the same specification with all class-based methods.

.. warning::

    A full list of methods can be found in the appropriate section of the documentation

.. autoclass:: aiogram.client.bot.Bot
    :members: __init__,token,id,context,me,download_file,download
    :show-inheritance:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True
