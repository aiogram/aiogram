##################
setChatDescription
##################

Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.set_chat_description
    :members:
    :member-order: bysource
    :special-members: __init__
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

- :code:`from aiogram.methods import SetChatDescription`
- :code:`from aiogram.api.methods import SetChatDescription`
- :code:`from aiogram.api.methods.set_chat_description import SetChatDescription`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetChatDescription(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetChatDescription(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetChatDescription(...)