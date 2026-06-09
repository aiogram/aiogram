######################
replaceManagedBotToken
######################

Returns: :obj:`str`

.. automodule:: aiogram.methods.replace_managed_bot_token
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: str = await bot.replace_managed_bot_token(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.replace_managed_bot_token import ReplaceManagedBotToken`
- alias: :code:`from aiogram.methods import ReplaceManagedBotToken`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: str = await bot(ReplaceManagedBotToken(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return ReplaceManagedBotToken(...)
