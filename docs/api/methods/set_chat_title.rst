############
setChatTitle
############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_chat_title
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_title(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_chat_title import SetChatTitle`
- alias: :code:`from aiogram.methods import SetChatTitle`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetChatTitle(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetChatTitle(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.set_title`
