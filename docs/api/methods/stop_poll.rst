########
stopPoll
########

Returns: :obj:`Poll`

.. automodule:: aiogram.methods.stop_poll
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Poll = await bot.stop_poll(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.stop_poll import StopPoll`
- alias: :code:`from aiogram.methods import StopPoll`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Poll = await bot(StopPoll(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return StopPoll(...)
