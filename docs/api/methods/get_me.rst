#####
getMe
#####

Returns: :obj:`BotFullInfo`

.. automodule:: aiogram.methods.get_me
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: BotFullInfo = await bot.get_me(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_me import GetMe`
- alias: :code:`from aiogram.methods import GetMe`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: BotFullInfo = await bot(GetMe(...))
