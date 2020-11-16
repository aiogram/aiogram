########
stopPoll
########

Use this method to stop a poll which was sent by the bot. On success, the stopped Poll with the final results is returned.

Returns: :obj:`Poll`

.. automodule:: aiogram.api.methods.stop_poll
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Poll = await bot.stop_poll(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import StopPoll`
- :code:`from aiogram.api.methods import StopPoll`
- :code:`from aiogram.api.methods.stop_poll import StopPoll`

In handlers with current bot
----------------------------

.. code-block::

    result: Poll = await StopPoll(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Poll = await bot(StopPoll(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return StopPoll(...)