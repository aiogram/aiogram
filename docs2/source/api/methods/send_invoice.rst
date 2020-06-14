###########
sendInvoice
###########

Use this method to send invoices. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.send_invoice
    :members:


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_invoice(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendInvoice`
- :code:`from aiogram.api.methods import SendInvoice`
- :code:`from aiogram.api.methods.send_invoice import SendInvoice`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendInvoice(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendInvoice(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendInvoice(...)