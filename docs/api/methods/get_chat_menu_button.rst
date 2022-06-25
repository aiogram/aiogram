#################
getChatMenuButton
#################

Returns: :obj:`MenuButton`

.. automodule:: aiogram.methods.get_chat_menu_button
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: MenuButton = await bot.get_chat_menu_button(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_chat_menu_button import GetChatMenuButton`
- alias: :code:`from aiogram.methods import GetChatMenuButton`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: MenuButton = await bot(GetChatMenuButton(...))
