#################
setChatMenuButton
#################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_chat_menu_button
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_menu_button(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_chat_menu_button import SetChatMenuButton`
- alias: :code:`from aiogram.methods import SetChatMenuButton`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetChatMenuButton(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetChatMenuButton(...)
