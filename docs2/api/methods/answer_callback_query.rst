###################
answerCallbackQuery
###################

Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to the user as a notification at the top of the chat screen or as an alert. On success, True is returned.

Alternatively, the user can be redirected to the specified Game URL. For this option to work, you must first create a game for your bot via @Botfather and accept the terms. Otherwise, you may use links like t.me/your_bot?start=XXXX that open your bot with a parameter.

Returns: :obj:`bool`

.. automodule:: aiogram.methods.answer_callback_query
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.answer_callback_query(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import AnswerCallbackQuery`
- :code:`from aiogram.methods import AnswerCallbackQuery`
- :code:`from aiogram.methods.answer_callback_query import AnswerCallbackQuery`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await AnswerCallbackQuery(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(AnswerCallbackQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return AnswerCallbackQuery(...)