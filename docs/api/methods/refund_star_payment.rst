#################
refundStarPayment
#################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.refund_star_payment
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.refund_star_payment(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.refund_star_payment import RefundStarPayment`
- alias: :code:`from aiogram.methods import RefundStarPayment`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(RefundStarPayment(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return RefundStarPayment(...)
