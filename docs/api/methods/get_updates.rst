##########
getUpdates
##########

Returns: :obj:`List[Update]`

.. automodule:: aiogram.methods.get_updates
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


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

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: List[Update] = await bot(GetUpdates(...))
