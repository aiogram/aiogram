############
setChatPhoto
############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_chat_photo
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_photo(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_chat_photo import SetChatPhoto`
- alias: :code:`from aiogram.methods import SetChatPhoto`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetChatPhoto(...))




As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.set_photo`
