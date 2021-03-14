##########
getUpdates
##########

Returns: :obj:`List[Update]`

.. automodule:: aiogram.methods.get_updates
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.get_updates import GetUpdates`
- alias: :code:`from aiogram.methods import GetUpdates`

In handlers with current bot
----------------------------

.. code-block:: python

    result: List[Update] = await GetUpdates(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: List[Update] = await bot(GetUpdates(...))
