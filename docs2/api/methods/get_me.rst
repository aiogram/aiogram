#####
getMe
#####

A simple method for testing your bot's auth token. Requires no parameters. Returns basic information about the bot in form of a User object.

Returns: :obj:`User`

.. automodule:: aiogram.methods.get_me
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


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
- :code:`from aiogram.methods import GetMe`
- :code:`from aiogram.methods.get_me import GetMe`

In handlers with current bot
----------------------------

.. code-block::

    result: User = await GetMe(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: User = await bot(GetMe(...))

