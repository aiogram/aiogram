###############################
setMyDefaultAdministratorRights
###############################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_my_default_administrator_rights
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_my_default_administrator_rights(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_my_default_administrator_rights import SetMyDefaultAdministratorRights`
- alias: :code:`from aiogram.methods import SetMyDefaultAdministratorRights`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetMyDefaultAdministratorRights(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetMyDefaultAdministratorRights(...)
