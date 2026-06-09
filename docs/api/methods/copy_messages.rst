############
copyMessages
############

Returns: :obj:`list[MessageId]`

.. automodule:: aiogram.methods.copy_messages
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: list[MessageId] = await bot.copy_messages(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.copy_messages import CopyMessages`
- alias: :code:`from aiogram.methods import CopyMessages`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: list[MessageId] = await bot(CopyMessages(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return CopyMessages(...)
