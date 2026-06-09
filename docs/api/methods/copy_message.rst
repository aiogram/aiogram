###########
copyMessage
###########

Returns: :obj:`MessageId`

.. automodule:: aiogram.methods.copy_message
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


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

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: MessageId = await bot(CopyMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return CopyMessage(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.copy_to`
