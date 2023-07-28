#####
close
#####

Returns: :obj:`bool`

.. automodule:: aiogram.methods.close
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.close(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.close import Close`
- alias: :code:`from aiogram.methods import Close`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(Close(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return Close(...)
