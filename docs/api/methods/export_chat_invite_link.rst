####################
exportChatInviteLink
####################

Returns: :obj:`str`

.. automodule:: aiogram.methods.export_chat_invite_link
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: str = await bot.export_chat_invite_link(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.export_chat_invite_link import ExportChatInviteLink`
- alias: :code:`from aiogram.methods import ExportChatInviteLink`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: str = await bot(ExportChatInviteLink(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return ExportChatInviteLink(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.export_invite_link`
