#######################
reopenGeneralForumTopic
#######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.reopen_general_forum_topic
    :members:
    :member-order: bysource
    :undoc-members: True


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.reopen_general_forum_topic(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.reopen_general_forum_topic import ReopenGeneralForumTopic`
- alias: :code:`from aiogram.methods import ReopenGeneralForumTopic`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(ReopenGeneralForumTopic(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return ReopenGeneralForumTopic(...)
