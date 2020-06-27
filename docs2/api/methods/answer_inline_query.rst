#################
answerInlineQuery
#################

Use this method to send answers to an inline query. On success, True is returned.

No more than 50 results per query are allowed.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.answer_inline_query
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.answer_inline_query(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import AnswerInlineQuery`
- :code:`from aiogram.api.methods import AnswerInlineQuery`
- :code:`from aiogram.api.methods.answer_inline_query import AnswerInlineQuery`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await AnswerInlineQuery(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(AnswerInlineQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return AnswerInlineQuery(...)