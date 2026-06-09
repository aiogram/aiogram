########
sendGift
########

Returns: :obj:`bool`

.. automodule:: aiogram.methods.send_gift
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.send_gift(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_gift import SendGift`
- alias: :code:`from aiogram.methods import SendGift`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SendGift(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendGift(...)
