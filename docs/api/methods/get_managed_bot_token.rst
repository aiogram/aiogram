##################
getManagedBotToken
##################

Returns: :obj:`str`

.. automodule:: aiogram.methods.get_managed_bot_token
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: str = await bot.get_managed_bot_token(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_managed_bot_token import GetManagedBotToken`
- alias: :code:`from aiogram.methods import GetManagedBotToken`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: str = await bot(GetManagedBotToken(...))
