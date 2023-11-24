============
Deep Linking
============

Telegram bots have a deep linking mechanism, that allows for passing
additional parameters to the bot on startup. It could be a command that
launches the bot — or an auth token to connect the user's Telegram
account to their account on some external service.

You can read detailed description in the source:
https://core.telegram.org/bots#deep-linking

We have added some utils to get deep links more handy.

Examples
========

Basic link example
------------------

.. code-block:: python

    from aiogram.utils.deep_linking import create_start_link

    link = await create_start_link(bot, 'foo')

    # result: 'https://t.me/MyBot?start=foo'

Encoded link
------------

.. code-block:: python

    from aiogram.utils.deep_linking import create_start_link

    link = await create_start_link(bot, 'foo', encode=True)
    # result: 'https://t.me/MyBot?start=Zm9v'

Decode it back
--------------

.. code-block:: python

    from aiogram.utils.deep_linking import decode_payload
    from aiogram.filters import CommandStart, CommandObject
    from aiogram.types import Message

    @router.message(CommandStart(deep_link=True))
    async def handler(message: Message, command: CommandObject):
        args = command.args
        payload = decode_payload(args)
        await message.answer(f"Your payload: {payload}")


References
==========

.. autofunction:: aiogram.utils.deep_linking.create_start_link

.. autofunction:: aiogram.utils.deep_linking.decode_payload
