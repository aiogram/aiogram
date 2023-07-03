##################
setStickerSetTitle
##################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_sticker_set_title
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_sticker_set_title(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_sticker_set_title import SetStickerSetTitle`
- alias: :code:`from aiogram.methods import SetStickerSetTitle`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetStickerSetTitle(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetStickerSetTitle(...)
