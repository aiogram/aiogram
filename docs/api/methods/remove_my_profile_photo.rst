####################
removeMyProfilePhoto
####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.remove_my_profile_photo
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.remove_my_profile_photo(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.remove_my_profile_photo import RemoveMyProfilePhoto`
- alias: :code:`from aiogram.methods import RemoveMyProfilePhoto`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(RemoveMyProfilePhoto(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return RemoveMyProfilePhoto(...)
