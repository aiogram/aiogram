##########################
answerChatJoinRequestQuery
##########################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.answer_chat_join_request_query
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.answer_chat_join_request_query(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.answer_chat_join_request_query import AnswerChatJoinRequestQuery`
- alias: :code:`from aiogram.methods import AnswerChatJoinRequestQuery`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(AnswerChatJoinRequestQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return AnswerChatJoinRequestQuery(...)
