######################
closeGeneralForumTopic
######################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.close_general_forum_topic
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.close_general_forum_topic(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.close_general_forum_topic import CloseGeneralForumTopic`
- alias: :code:`from aiogram.methods import CloseGeneralForumTopic`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(CloseGeneralForumTopic(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return CloseGeneralForumTopic(...)
