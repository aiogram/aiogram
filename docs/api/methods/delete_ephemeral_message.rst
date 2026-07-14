######################
deleteEphemeralMessage
######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_ephemeral_message
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_ephemeral_message(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_ephemeral_message import DeleteEphemeralMessage`
- alias: :code:`from aiogram.methods import DeleteEphemeralMessage`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteEphemeralMessage(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteEphemeralMessage(...)
