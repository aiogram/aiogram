###############################
setMyDefaultAdministratorRights
###############################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_my_default_administrator_rights
    :members:
    :member-order: bysource
    :undoc-members: True


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

In handlers with current bot
----------------------------

.. code-block:: python

    result: bool = await SetMyDefaultAdministratorRights(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetMyDefaultAdministratorRights(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetMyDefaultAdministratorRights(...)
