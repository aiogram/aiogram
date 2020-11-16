#########
sendPhoto
#########

Use this method to send photos. On success, the sent Message is returned.

Returns: :obj:`Message`

.. automodule:: aiogram.api.methods.send_photo
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_photo(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import SendPhoto`
- :code:`from aiogram.api.methods import SendPhoto`
- :code:`from aiogram.api.methods.send_photo import SendPhoto`

In handlers with current bot
----------------------------

.. code-block::

    result: Message = await SendPhoto(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: Message = await bot(SendPhoto(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block::

    return SendPhoto(...)