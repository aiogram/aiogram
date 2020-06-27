####################
getUserProfilePhotos
####################

Use this method to get a list of profile pictures for a user. Returns a UserProfilePhotos object.

Returns: :obj:`UserProfilePhotos`

.. automodule:: aiogram.api.methods.get_user_profile_photos
    :members:
    :member-order: bysource
    :special-members: __init__
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: UserProfilePhotos = await bot.get_user_profile_photos(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods import GetUserProfilePhotos`
- :code:`from aiogram.api.methods import GetUserProfilePhotos`
- :code:`from aiogram.api.methods.get_user_profile_photos import GetUserProfilePhotos`

In handlers with current bot
----------------------------

.. code-block::

    result: UserProfilePhotos = await GetUserProfilePhotos(...)

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block::

    result: UserProfilePhotos = await bot(GetUserProfilePhotos(...))

