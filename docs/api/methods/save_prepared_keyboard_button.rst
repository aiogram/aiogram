##########################
savePreparedKeyboardButton
##########################

Returns: :obj:`PreparedKeyboardButton`

.. automodule:: aiogram.methods.save_prepared_keyboard_button
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: PreparedKeyboardButton = await bot.save_prepared_keyboard_button(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.save_prepared_keyboard_button import SavePreparedKeyboardButton`
- alias: :code:`from aiogram.methods import SavePreparedKeyboardButton`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: PreparedKeyboardButton = await bot(SavePreparedKeyboardButton(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SavePreparedKeyboardButton(...)
