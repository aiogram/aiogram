###################
answerShippingQuery
###################

If you sent an invoice requesting a shipping address and the parameter is_flexible was specified, the Bot API will send an Update with a shipping_query field to the bot. Use this method to reply to shipping queries. On success, True is returned.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.answer_shipping_query
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.answer_shipping_query(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import AnswerShippingQuery`
- :code:`from aiogram.api.methods import AnswerShippingQuery`
- :code:`from aiogram.api.methods.answer_shipping_query import AnswerShippingQuery`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await AnswerShippingQuery(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(AnswerShippingQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return AnswerShippingQuery(...)