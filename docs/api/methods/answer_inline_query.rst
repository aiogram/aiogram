#################
answerInlineQuery
#################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.answer_inline_query
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


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

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(AnswerInlineQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return AnswerInlineQuery(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.inline_query.InlineQuery.answer`
