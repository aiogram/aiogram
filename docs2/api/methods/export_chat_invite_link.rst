####################
exportChatInviteLink
####################

Returns: :obj:`str`

.. automodule:: aiogram.methods.export_chat_invite_link
    :members:
    :member-order: bysource
    :undoc-members: True


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

In handlers with current bot
----------------------------

.. code-block:: python

    result: str = await ExportChatInviteLink(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: str = await bot(ExportChatInviteLink(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return ExportChatInviteLink(...)