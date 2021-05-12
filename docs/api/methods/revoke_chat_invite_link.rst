####################
revokeChatInviteLink
####################

Returns: :obj:`ChatInviteLink`

.. automodule:: aiogram.methods.revoke_chat_invite_link
    :members:
    :member-order: bysource
    :undoc-members: True


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

In handlers with current bot
----------------------------

.. code-block:: python

    result: ChatInviteLink = await RevokeChatInviteLink(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ChatInviteLink = await bot(RevokeChatInviteLink(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return RevokeChatInviteLink(...)
