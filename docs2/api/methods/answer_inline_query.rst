#################
answerInlineQuery
#################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.answer_inline_query
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.answer_inline_query import AnswerInlineQuery`
- alias: :code:`from aiogram.methods import AnswerInlineQuery`

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await AnswerInlineQuery(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(AnswerInlineQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return AnswerInlineQuery(...)