#####
getMe
#####

A simple method for testing your bot's auth token. Requires no parameters. Returns basic information about the bot in form of a User object.

Returns: :obj:`User`

.. automodule:: aiogram.api.methods.get_me
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: User = await bot.get_me(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import GetMe`
- :code:`from aiogram.api.methods import GetMe`
- :code:`from aiogram.api.methods.get_me import GetMe`

In handlers with current bot
----------------------------

.. code-block::

    result: User = await GetMe(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: User = await bot(GetMe(...))

