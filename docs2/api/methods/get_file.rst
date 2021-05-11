#######
getFile
#######

Returns: :obj:`File`

.. automodule:: aiogram.methods.get_file
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.get_file import GetFile`
- alias: :code:`from aiogram.methods import GetFile`

In handlers with current bot
----------------------------

.. code-block:: python

    result: File = await GetFile(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: File = await bot(GetFile(...))
