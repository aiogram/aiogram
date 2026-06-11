###############
sendRichMessage
###############

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_rich_message
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_rich_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_rich_message import SendRichMessage`
- alias: :code:`from aiogram.methods import SendRichMessage`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendRichMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendRichMessage(...)
