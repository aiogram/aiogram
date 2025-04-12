#####################
setBusinessAccountBio
#####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_business_account_bio
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_business_account_bio(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_business_account_bio import SetBusinessAccountBio`
- alias: :code:`from aiogram.methods import SetBusinessAccountBio`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetBusinessAccountBio(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetBusinessAccountBio(...)
