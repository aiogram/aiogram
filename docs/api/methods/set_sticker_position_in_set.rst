#######################
setStickerPositionInSet
#######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_sticker_position_in_set
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_sticker_position_in_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_sticker_position_in_set import SetStickerPositionInSet`
- alias: :code:`from aiogram.methods import SetStickerPositionInSet`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetStickerPositionInSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetStickerPositionInSet(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.sticker.Sticker.set_position_in_set`
