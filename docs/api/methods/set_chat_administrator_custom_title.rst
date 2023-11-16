###############################
setChatAdministratorCustomTitle
###############################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_chat_administrator_custom_title
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_administrator_custom_title(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_chat_administrator_custom_title import SetChatAdministratorCustomTitle`
- alias: :code:`from aiogram.methods import SetChatAdministratorCustomTitle`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetChatAdministratorCustomTitle(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetChatAdministratorCustomTitle(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.set_administrator_custom_title`
