##########
getUpdates
##########

Use this method to receive incoming updates using long polling (wiki). An Array of Update objects is returned.

Notes

1. This method will not work if an outgoing webhook is set up.

2. In order to avoid getting duplicate updates, recalculate offset after each server response.

Returns: :obj:`List[Update]`

.. automodule:: aiogram.methods.get_updates
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: List[Update] = await bot.get_updates(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import GetUpdates`
- :code:`from aiogram.methods import GetUpdates`
- :code:`from aiogram.methods.get_updates import GetUpdates`

In handlers with current bot
----------------------------

.. code-block::

    result: List[Update] = await GetUpdates(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: List[Update] = await bot(GetUpdates(...))

