#########
leaveChat
#########

Returns: :obj:`bool`

.. automodule:: aiogram.methods.leave_chat
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.leave_chat(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.leave_chat import LeaveChat`
- alias: :code:`from aiogram.methods import LeaveChat`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(LeaveChat(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return LeaveChat(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.chat.Chat.leave`
