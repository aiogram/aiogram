#####################
deleteMessageReaction
#####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_message_reaction
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_message_reaction(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_message_reaction import DeleteMessageReaction`
- alias: :code:`from aiogram.methods import DeleteMessageReaction`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteMessageReaction(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteMessageReaction(...)
