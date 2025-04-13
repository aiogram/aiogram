###################
readBusinessMessage
###################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.read_business_message
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.read_business_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.read_business_message import ReadBusinessMessage`
- alias: :code:`from aiogram.methods import ReadBusinessMessage`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(ReadBusinessMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return ReadBusinessMessage(...)
