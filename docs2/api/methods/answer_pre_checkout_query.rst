######################
answerPreCheckoutQuery
######################

Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an Update with the field pre_checkout_query. Use this method to respond to such pre-checkout queries. On success, True is returned. Note: The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.

Returns: :obj:`bool`

.. automodule:: aiogram.methods.answer_pre_checkout_query
    :members:
    :member-order: bysource
    :special-members: __init__
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

- :code:`from aiogram.methods import AnswerPreCheckoutQuery`
- :code:`from aiogram.methods import AnswerPreCheckoutQuery`
- :code:`from aiogram.methods.answer_pre_checkout_query import AnswerPreCheckoutQuery`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await AnswerPreCheckoutQuery(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(AnswerPreCheckoutQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return AnswerPreCheckoutQuery(...)