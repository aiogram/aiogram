############
sendDocument
############

Use this method to send general files. On success, the sent Message is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_document
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_document(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendDocument`
- :code:`from aiogram.methods import SendDocument`
- :code:`from aiogram.methods.send_document import SendDocument`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendDocument(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendDocument(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendDocument(...)