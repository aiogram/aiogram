####################
revokeChatInviteLink
####################

Returns: :obj:`ChatInviteLink`

.. automodule:: aiogram.methods.revoke_chat_invite_link
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: ChatInviteLink = await bot.revoke_chat_invite_link(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.revoke_chat_invite_link import RevokeChatInviteLink`
- alias: :code:`from aiogram.methods import RevokeChatInviteLink`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ChatInviteLink = await bot(RevokeChatInviteLink(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return RevokeChatInviteLink(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.revoke_invite_link`
