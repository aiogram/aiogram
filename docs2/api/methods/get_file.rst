#######
getFile
#######

Use this method to get basic info about a file and prepare it for downloading. For the moment, bots can download files of up to 20MB in size. On success, a File object is returned. The file can then be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>, where <file_path> is taken from the response. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling getFile again.

Note: This function may not preserve the original file name and MIME type. You should save the file's MIME type and name (if available) when the File object is received.

Returns: :obj:`File`

.. automodule:: aiogram.api.methods.get_file
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: File = await bot.get_file(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import GetFile`
- :code:`from aiogram.api.methods import GetFile`
- :code:`from aiogram.api.methods.get_file import GetFile`

In handlers with current bot
----------------------------

.. code-block::

    result: File = await GetFile(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: File = await bot(GetFile(...))

