################
answerGuestQuery
################

Returns: :obj:`SentGuestMessage`

.. automodule:: aiogram.methods.answer_guest_query
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: SentGuestMessage = await bot.answer_guest_query(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.answer_guest_query import AnswerGuestQuery`
- alias: :code:`from aiogram.methods import AnswerGuestQuery`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: SentGuestMessage = await bot(AnswerGuestQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return AnswerGuestQuery(...)
