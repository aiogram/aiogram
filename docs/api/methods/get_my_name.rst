#########
getMyName
#########

Returns: :obj:`BotName`

.. automodule:: aiogram.methods.get_my_name
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: BotName = await bot.get_my_name(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_my_name import GetMyName`
- alias: :code:`from aiogram.methods import GetMyName`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: BotName = await bot(GetMyName(...))
