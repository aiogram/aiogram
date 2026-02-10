#################
setMyProfilePhoto
#################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.set_my_profile_photo
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.set_my_profile_photo(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.set_my_profile_photo import SetMyProfilePhoto`
- alias: :code:`from aiogram.methods import SetMyProfilePhoto`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(SetMyProfilePhoto(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return SetMyProfilePhoto(...)
