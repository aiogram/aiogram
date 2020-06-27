##################
setChatPermissions
##################

Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the can_restrict_members admin rights. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.set_chat_permissions
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_chat_permissions(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SetChatPermissions`
- :code:`from aiogram.api.methods import SetChatPermissions`
- :code:`from aiogram.api.methods.set_chat_permissions import SetChatPermissions`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetChatPermissions(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetChatPermissions(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetChatPermissions(...)