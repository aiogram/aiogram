#########################
savePreparedInlineMessage
#########################

Returns: :obj:`PreparedInlineMessage`

.. automodule:: aiogram.methods.save_prepared_inline_message
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: PreparedInlineMessage = await bot.save_prepared_inline_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.save_prepared_inline_message import SavePreparedInlineMessage`
- alias: :code:`from aiogram.methods import SavePreparedInlineMessage`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: PreparedInlineMessage = await bot(SavePreparedInlineMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SavePreparedInlineMessage(...)
