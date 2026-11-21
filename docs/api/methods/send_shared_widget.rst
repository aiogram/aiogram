################
sendSharedWidget
################

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_shared_widget
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_shared_widget(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_shared_widget import SendSharedWidget`
- alias: :code:`from aiogram.methods import SendSharedWidget`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendSharedWidget(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendSharedWidget(...)
