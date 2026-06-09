#################
getChatMenuButton
#################

Returns: :obj:`ResultMenuButtonUnion`

.. automodule:: aiogram.methods.get_chat_menu_button
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: ResultMenuButtonUnion = await bot.get_chat_menu_button(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_chat_menu_button import GetChatMenuButton`
- alias: :code:`from aiogram.methods import GetChatMenuButton`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ResultMenuButtonUnion = await bot(GetChatMenuButton(...))
