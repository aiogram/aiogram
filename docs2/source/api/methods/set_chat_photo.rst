############
setChatPhoto
############

Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.set_chat_photo
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_photo(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SetChatPhoto`
- :code:`from aiogram.api.methods import SetChatPhoto`
- :code:`from aiogram.api.methods.set_chat_photo import SetChatPhoto`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetChatPhoto(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetChatPhoto(...))

