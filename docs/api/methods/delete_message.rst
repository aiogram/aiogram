#############
deleteMessage
#############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_message
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_message import DeleteMessage`
- alias: :code:`from aiogram.methods import DeleteMessage`

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await DeleteMessage(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteMessage(...)
