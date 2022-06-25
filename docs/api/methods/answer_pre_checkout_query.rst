######################
answerPreCheckoutQuery
######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.answer_pre_checkout_query
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.answer_pre_checkout_query(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.answer_pre_checkout_query import AnswerPreCheckoutQuery`
- alias: :code:`from aiogram.methods import AnswerPreCheckoutQuery`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(AnswerPreCheckoutQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return AnswerPreCheckoutQuery(...)
