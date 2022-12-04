##################
setChatDescription
##################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_chat_description
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_description(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_chat_description import SetChatDescription`
- alias: :code:`from aiogram.methods import SetChatDescription`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetChatDescription(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetChatDescription(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.set_description`
