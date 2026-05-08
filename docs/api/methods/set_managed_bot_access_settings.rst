###########################
setManagedBotAccessSettings
###########################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_managed_bot_access_settings
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_managed_bot_access_settings(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_managed_bot_access_settings import SetManagedBotAccessSettings`
- alias: :code:`from aiogram.methods import SetManagedBotAccessSettings`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetManagedBotAccessSettings(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetManagedBotAccessSettings(...)
