#########
leaveChat
#########

Use this method for your bot to leave a group, supergroup or channel. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.methods.leave_chat
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.leave_chat(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import LeaveChat`
- :code:`from aiogram.methods import LeaveChat`
- :code:`from aiogram.methods.leave_chat import LeaveChat`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await LeaveChat(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(LeaveChat(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return LeaveChat(...)