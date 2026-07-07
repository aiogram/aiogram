###########################
getManagedBotAccessSettings
###########################

Returns: :obj:`BotAccessSettings`

.. automodule:: aiogram.methods.get_managed_bot_access_settings
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: BotAccessSettings = await bot.get_managed_bot_access_settings(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_managed_bot_access_settings import GetManagedBotAccessSettings`
- alias: :code:`from aiogram.methods import GetManagedBotAccessSettings`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: BotAccessSettings = await bot(GetManagedBotAccessSettings(...))
