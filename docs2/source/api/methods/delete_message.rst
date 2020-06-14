#############
deleteMessage
#############

Use this method to delete a message, including service messages, with the following limitations:

- A message can only be deleted if it was sent less than 48 hours ago.

- A dice message in a private chat can only be deleted if it was sent more than 24 hours ago.

- Bots can delete outgoing messages in private chats, groups, and supergroups.

- Bots can delete incoming messages in private chats.

- Bots granted can_post_messages permissions can delete outgoing messages in channels.

- If the bot is an administrator of a group, it can delete any message there.

- If the bot has can_delete_messages permission in a supergroup or a channel, it can delete any message there.

Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.delete_message
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import DeleteMessage`
- :code:`from aiogram.api.methods import DeleteMessage`
- :code:`from aiogram.api.methods.delete_message import DeleteMessage`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await DeleteMessage(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(DeleteMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return DeleteMessage(...)