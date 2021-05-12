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

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await SetChatPhoto(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetChatPhoto(...))
