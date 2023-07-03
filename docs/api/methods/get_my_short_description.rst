#####################
getMyShortDescription
#####################

Returns: :obj:`BotShortDescription`

.. automodule:: aiogram.methods.get_my_short_description
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: BotShortDescription = await bot.get_my_short_description(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_my_short_description import GetMyShortDescription`
- alias: :code:`from aiogram.methods import GetMyShortDescription`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: BotShortDescription = await bot(GetMyShortDescription(...))
