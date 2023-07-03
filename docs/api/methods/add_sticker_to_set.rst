###############
addStickerToSet
###############

Returns: :obj:`bool`

.. automodule:: aiogram.methods.add_sticker_to_set
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.add_sticker_to_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.add_sticker_to_set import AddStickerToSet`
- alias: :code:`from aiogram.methods import AddStickerToSet`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(AddStickerToSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return AddStickerToSet(...)
