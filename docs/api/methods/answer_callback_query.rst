###################
answerCallbackQuery
###################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.answer_callback_query
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.answer_callback_query(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.answer_callback_query import AnswerCallbackQuery`
- alias: :code:`from aiogram.methods import AnswerCallbackQuery`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(AnswerCallbackQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return AnswerCallbackQuery(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.callback_query.CallbackQuery.answer`
