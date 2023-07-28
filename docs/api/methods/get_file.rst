#######
getFile
#######

Returns: :obj:`File`

.. automodule:: aiogram.methods.get_file
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


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

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: File = await bot(GetFile(...))
