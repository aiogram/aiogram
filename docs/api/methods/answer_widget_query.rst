#################
answerWidgetQuery
#################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.answer_widget_query
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.answer_widget_query(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.answer_widget_query import AnswerWidgetQuery`
- alias: :code:`from aiogram.methods import AnswerWidgetQuery`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(AnswerWidgetQuery(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return AnswerWidgetQuery(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.shared_widget_query.SharedWidgetQuery.answer`
- :meth:`aiogram.types.widget_query.WidgetQuery.answer`
