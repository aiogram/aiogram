###############################
getMyDefaultAdministratorRights
###############################

Returns: :obj:`ChatAdministratorRights`

.. automodule:: aiogram.methods.get_my_default_administrator_rights
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: ChatAdministratorRights = await bot.get_my_default_administrator_rights(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_my_default_administrator_rights import GetMyDefaultAdministratorRights`
- alias: :code:`from aiogram.methods import GetMyDefaultAdministratorRights`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: ChatAdministratorRights = await bot(GetMyDefaultAdministratorRights(...))
