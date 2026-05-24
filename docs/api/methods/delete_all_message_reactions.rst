#########################
deleteAllMessageReactions
#########################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.delete_all_message_reactions
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.delete_all_message_reactions(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.delete_all_message_reactions import DeleteAllMessageReactions`
- alias: :code:`from aiogram.methods import DeleteAllMessageReactions`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeleteAllMessageReactions(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeleteAllMessageReactions(...)
