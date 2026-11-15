##########
sendWidget
##########

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_widget
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_widget(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_widget import SendWidget`
- alias: :code:`from aiogram.methods import SendWidget`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendWidget(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendWidget(...)
