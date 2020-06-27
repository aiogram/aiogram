#######
getChat
#######

Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a Chat object on success.

Returns: :obj:`Chat`

.. automodule:: aiogram.api.methods.get_chat
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Chat = await bot.get_chat(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import GetChat`
- :code:`from aiogram.api.methods import GetChat`
- :code:`from aiogram.api.methods.get_chat import GetChat`

In handlers with current bot
----------------------------

.. code-block::

    result: Chat = await GetChat(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Chat = await bot(GetChat(...))

