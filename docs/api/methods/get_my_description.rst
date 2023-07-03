################
getMyDescription
################

Returns: :obj:`BotDescription`

.. automodule:: aiogram.methods.get_my_description
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: BotDescription = await bot.get_my_description(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_my_description import GetMyDescription`
- alias: :code:`from aiogram.methods import GetMyDescription`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: BotDescription = await bot(GetMyDescription(...))
