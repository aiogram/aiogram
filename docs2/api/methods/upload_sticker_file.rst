#################
uploadStickerFile
#################

Returns: :obj:`File`

.. automodule:: aiogram.methods.upload_sticker_file
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: File = await bot.upload_sticker_file(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.upload_sticker_file import UploadStickerFile`
- alias: :code:`from aiogram.methods import UploadStickerFile`

In handlers with current bot
----------------------------

.. code-block:: python

    result: File = await UploadStickerFile(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: File = await bot(UploadStickerFile(...))
