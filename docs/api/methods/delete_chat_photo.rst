###############
deleteChatPhoto
###############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_chat_photo
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


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

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteChatPhoto(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteChatPhoto(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.delete_photo`
