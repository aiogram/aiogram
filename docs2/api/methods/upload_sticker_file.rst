#################
uploadStickerFile
#################

Use this method to upload a .PNG file with a sticker for later use in createNewStickerSet and addStickerToSet methods (can be used multiple times). Returns the uploaded File on success.

Returns: :obj:`File`

.. automodule:: aiogram.api.methods.upload_sticker_file
    :members:
    :member-order: bysource
    :special-members: __init__
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

- :code:`from aiogram.methods import UploadStickerFile`
- :code:`from aiogram.api.methods import UploadStickerFile`
- :code:`from aiogram.api.methods.upload_sticker_file import UploadStickerFile`

In handlers with current bot
----------------------------

.. code-block::

    result: File = await UploadStickerFile(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: File = await bot(UploadStickerFile(...))

