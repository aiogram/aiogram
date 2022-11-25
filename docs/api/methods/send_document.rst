############
sendDocument
############

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_document
    :members:
    :member-order: bysource
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

- :code:`from aiogram.methods.send_document import SendDocument`
- alias: :code:`from aiogram.methods import SendDocument`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendDocument(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendDocument(...)


As shortcut from received object
--------------------------------

- :meth:`aiogram.types.message.Message.answer_document`
- :meth:`aiogram.types.message.Message.reply_document`
