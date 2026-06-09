##############################
editChatSubscriptionInviteLink
##############################

Returns: :obj:`ChatInviteLink`

.. automodule:: aiogram.methods.edit_chat_subscription_invite_link
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: ChatInviteLink = await bot.edit_chat_subscription_invite_link(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.edit_chat_subscription_invite_link import EditChatSubscriptionInviteLink`
- alias: :code:`from aiogram.methods import EditChatSubscriptionInviteLink`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ChatInviteLink = await bot(EditChatSubscriptionInviteLink(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return EditChatSubscriptionInviteLink(...)
