#######################
setStickerPositionInSet
#######################

Use this method to move a sticker in a set created by the bot to a specific position. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_sticker_position_in_set
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_sticker_position_in_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SetStickerPositionInSet`
- :code:`from aiogram.methods import SetStickerPositionInSet`
- :code:`from aiogram.methods.set_sticker_position_in_set import SetStickerPositionInSet`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetStickerPositionInSet(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetStickerPositionInSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetStickerPositionInSet(...)