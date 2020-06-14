##################
setStickerSetThumb
##################

Use this method to set the thumbnail of a sticker set. Animated thumbnails can be set for animated sticker sets only. Returns True on success.

Returns: :obj:`bool`

.. automodule:: aiogram.api.methods.set_sticker_set_thumb
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_sticker_set_thumb(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SetStickerSetThumb`
- :code:`from aiogram.api.methods import SetStickerSetThumb`
- :code:`from aiogram.api.methods.set_sticker_set_thumb import SetStickerSetThumb`

In handlers with current bot
----------------------------

.. code-block::

    result: bool = await SetStickerSetThumb(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: bool = await bot(SetStickerSetThumb(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SetStickerSetThumb(...)