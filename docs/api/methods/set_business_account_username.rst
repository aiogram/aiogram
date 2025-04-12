##########################
setBusinessAccountUsername
##########################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_business_account_username
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_business_account_username(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_business_account_username import SetBusinessAccountUsername`
- alias: :code:`from aiogram.methods import SetBusinessAccountUsername`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetBusinessAccountUsername(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetBusinessAccountUsername(...)
