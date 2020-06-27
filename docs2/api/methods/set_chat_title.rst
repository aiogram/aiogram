############
setChatTitle
############

Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.set_chat_title
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_title(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SetChatTitle`
- :code:`from aiogram.api.methods import SetChatTitle`
- :code:`from aiogram.api.methods.set_chat_title import SetChatTitle`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetChatTitle(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetChatTitle(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetChatTitle(...)