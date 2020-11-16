###############################
setChatAdministratorCustomTitle
###############################

Use this method to set a custom title for an administrator in a supergroup promoted by the bot. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.set_chat_administrator_custom_title
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_administrator_custom_title(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SetChatAdministratorCustomTitle`
- :code:`from aiogram.api.methods import SetChatAdministratorCustomTitle`
- :code:`from aiogram.api.methods.set_chat_administrator_custom_title import SetChatAdministratorCustomTitle`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetChatAdministratorCustomTitle(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetChatAdministratorCustomTitle(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetChatAdministratorCustomTitle(...)