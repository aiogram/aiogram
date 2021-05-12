###############
deleteChatPhoto
###############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_chat_photo
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.delete_chat_photo import DeleteChatPhoto`
- alias: :code:`from aiogram.methods import DeleteChatPhoto`

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await DeleteChatPhoto(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteChatPhoto(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteChatPhoto(...)
