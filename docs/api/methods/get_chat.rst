#######
getChat
#######

Returns: :obj:`ChatFullInfo`

.. automodule:: aiogram.methods.get_chat
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: ChatFullInfo = await bot.get_chat(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_chat import GetChat`
- alias: :code:`from aiogram.methods import GetChat`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ChatFullInfo = await bot(GetChat(...))
