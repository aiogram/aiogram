###############
deleteChatPhoto
###############

Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.delete_chat_photo
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_chat_photo(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import DeleteChatPhoto`
- :code:`from aiogram.api.methods import DeleteChatPhoto`
- :code:`from aiogram.api.methods.delete_chat_photo import DeleteChatPhoto`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await DeleteChatPhoto(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(DeleteChatPhoto(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return DeleteChatPhoto(...)