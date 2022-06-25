#######
getChat
#######

Returns: :obj:`Chat`

.. automodule:: aiogram.methods.get_chat
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Chat = await bot.get_chat(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_chat import GetChat`
- alias: :code:`from aiogram.methods import GetChat`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Chat = await bot(GetChat(...))
