#####################
getBusinessConnection
#####################

Returns: :obj:`BusinessConnection`

.. automodule:: aiogram.methods.get_business_connection
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: BusinessConnection = await bot.get_business_connection(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_business_connection import GetBusinessConnection`
- alias: :code:`from aiogram.methods import GetBusinessConnection`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: BusinessConnection = await bot(GetBusinessConnection(...))
