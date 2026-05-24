#############
sendLivePhoto
#############

Returns: :obj:`Message`

.. automodule:: aiogram.methods.send_live_photo
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: Message = await bot.send_live_photo(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.send_live_photo import SendLivePhoto`
- alias: :code:`from aiogram.methods import SendLivePhoto`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: Message = await bot(SendLivePhoto(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SendLivePhoto(...)
