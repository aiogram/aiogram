##################
setStickerKeywords
##################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_sticker_keywords
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_sticker_keywords(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_sticker_keywords import SetStickerKeywords`
- alias: :code:`from aiogram.methods import SetStickerKeywords`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetStickerKeywords(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetStickerKeywords(...)
