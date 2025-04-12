######################
setBusinessAccountName
######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_business_account_name
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_business_account_name(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_business_account_name import SetBusinessAccountName`
- alias: :code:`from aiogram.methods import SetBusinessAccountName`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetBusinessAccountName(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetBusinessAccountName(...)
