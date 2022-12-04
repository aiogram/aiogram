############
setChatPhoto
############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_chat_photo
    :members:
    :member-order: bysource
    :undoc-members: True


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
