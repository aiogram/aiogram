####################
declineSuggestedPost
####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.decline_suggested_post
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.decline_suggested_post(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.decline_suggested_post import DeclineSuggestedPost`
- alias: :code:`from aiogram.methods import DeclineSuggestedPost`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(DeclineSuggestedPost(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return DeclineSuggestedPost(...)
