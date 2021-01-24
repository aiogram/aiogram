###################
answerShippingQuery
###################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.answer_shipping_query
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.answer_shipping_query import AnswerShippingQuery`
- alias: :code:`from aiogram.methods import AnswerShippingQuery`

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await AnswerShippingQuery(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(AnswerShippingQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return AnswerShippingQuery(...)