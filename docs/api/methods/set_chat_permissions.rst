##################
setChatPermissions
##################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_chat_permissions
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.set_chat_permissions import SetChatPermissions`
- alias: :code:`from aiogram.methods import SetChatPermissions`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetChatPermissions(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetChatPermissions(...)
