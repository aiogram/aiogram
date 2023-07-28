#####################
setPassportDataErrors
#####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_passport_data_errors
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_passport_data_errors(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_passport_data_errors import SetPassportDataErrors`
- alias: :code:`from aiogram.methods import SetPassportDataErrors`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetPassportDataErrors(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetPassportDataErrors(...)
