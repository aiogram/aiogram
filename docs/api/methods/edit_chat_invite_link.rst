##################
editChatInviteLink
##################

Returns: :obj:`ChatInviteLink`

.. automodule:: aiogram.methods.edit_chat_invite_link
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: ChatInviteLink = await bot.edit_chat_invite_link(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_chat_invite_link import EditChatInviteLink`
- alias: :code:`from aiogram.methods import EditChatInviteLink`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ChatInviteLink = await bot(EditChatInviteLink(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditChatInviteLink(...)
