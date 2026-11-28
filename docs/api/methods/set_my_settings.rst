#############
setMySettings
#############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_my_settings
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_my_settings(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_my_settings import SetMySettings`
- alias: :code:`from aiogram.methods import SetMySettings`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetMySettings(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetMySettings(...)
