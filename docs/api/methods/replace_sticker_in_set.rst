###################
replaceStickerInSet
###################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.replace_sticker_in_set
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.replace_sticker_in_set(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.replace_sticker_in_set import ReplaceStickerInSet`
- alias: :code:`from aiogram.methods import ReplaceStickerInSet`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(ReplaceStickerInSet(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return ReplaceStickerInSet(...)
