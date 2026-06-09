####################
createChatInviteLink
####################

Returns: :obj:`ChatInviteLink`

.. automodule:: aiogram.methods.create_chat_invite_link
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: ChatInviteLink = await bot.create_chat_invite_link(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.create_chat_invite_link import CreateChatInviteLink`
- alias: :code:`from aiogram.methods import CreateChatInviteLink`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ChatInviteLink = await bot(CreateChatInviteLink(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return CreateChatInviteLink(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.create_invite_link`
