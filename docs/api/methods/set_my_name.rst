#########
setMyName
#########

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_my_name
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_my_name(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_my_name import SetMyName`
- alias: :code:`from aiogram.methods import SetMyName`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetMyName(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetMyName(...)
