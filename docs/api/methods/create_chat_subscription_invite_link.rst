################################
createChatSubscriptionInviteLink
################################

Returns: :obj:`ChatInviteLink`

.. automodule:: aiogram.methods.create_chat_subscription_invite_link
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: ChatInviteLink = await bot.create_chat_subscription_invite_link(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.create_chat_subscription_invite_link import CreateChatSubscriptionInviteLink`
- alias: :code:`from aiogram.methods import CreateChatSubscriptionInviteLink`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ChatInviteLink = await bot(CreateChatSubscriptionInviteLink(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return CreateChatSubscriptionInviteLink(...)
