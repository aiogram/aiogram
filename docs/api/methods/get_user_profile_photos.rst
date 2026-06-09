####################
getUserProfilePhotos
####################

Returns: :obj:`UserProfilePhotos`

.. automodule:: aiogram.methods.get_user_profile_photos
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: UserProfilePhotos = await bot.get_user_profile_photos(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.get_user_profile_photos import GetUserProfilePhotos`
- alias: :code:`from aiogram.methods import GetUserProfilePhotos`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: UserProfilePhotos = await bot(GetUserProfilePhotos(...))




As shortcut from received object
--------------------------------

- :meth:`aiogram.types.user.User.get_profile_photos`
