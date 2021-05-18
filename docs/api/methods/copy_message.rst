###########
copyMessage
###########

Returns: :obj:`MessageId`

.. automodule:: aiogram.methods.copy_message
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: MessageId = await bot.copy_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.copy_message import CopyMessage`
- alias: :code:`from aiogram.methods import CopyMessage`

In handlers with current bot
----------------------------

.. code-block:: python

    result: MessageId = await CopyMessage(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: MessageId = await bot(CopyMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return CopyMessage(...)
