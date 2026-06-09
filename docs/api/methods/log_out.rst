######
logOut
######

Returns: :obj:`bool`

.. automodule:: aiogram.methods.log_out
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.log_out(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.log_out import LogOut`
- alias: :code:`from aiogram.methods import LogOut`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(LogOut(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return LogOut(...)
