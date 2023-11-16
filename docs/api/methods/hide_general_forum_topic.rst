#####################
hideGeneralForumTopic
#####################

Returns: :obj:`bool`

.. automodule:: aiogram.methods.hide_general_forum_topic
    :members:
    :member-order: bysource
    :undoc-members: True
    :exclude-members: model_config,model_fields


Usage
=====

As bot method
-------------

.. code-block::

    result: bool = await bot.hide_general_forum_topic(...)


Method as object
----------------

Imports:

- :code:`from aiogram.methods.hide_general_forum_topic import HideGeneralForumTopic`
- alias: :code:`from aiogram.methods import HideGeneralForumTopic`

With specific bot
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result: bool = await bot(HideGeneralForumTopic(...))

As reply into Webhook in handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    return HideGeneralForumTopic(...)
