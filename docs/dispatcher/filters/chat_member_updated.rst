=================
ChatMemberUpdated
=================

Usage
=====

Handle user leave or join events

.. code-block:: python

    from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER

    @router.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
    async def on_user_leave(event: ChatMemberUpdated): ...

    @router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
    async def on_user_join(event: ChatMemberUpdated): ...

Or construct your own terms via using pre-defined set of statuses and transitions.


Explanation
===========

.. autoclass:: aiogram.filters.chat_member_updated.ChatMemberUpdatedFilter
    :members:
    :member-order: bysource
    :undoc-members: False

You can import from :code:`aiogram.filters` all available
variants of `statuses`_, `status groups`_ or `transitions`_:

Statuses
========

+-------------------------+--------------------------------------+
| name                    | Description                          |
+=========================+======================================+
| :code:`CREATOR`         | Chat owner                           |
+-------------------------+--------------------------------------+
| :code:`ADMINISTRATOR`   | Chat administrator                   |
+-------------------------+--------------------------------------+
| :code:`MEMBER`          | Member of the chat                   |
+-------------------------+--------------------------------------+
| :code:`RESTRICTED`      | Restricted user (can be not member)  |
+-------------------------+--------------------------------------+
| :code:`LEFT`            | Isn't member of the chat             |
+-------------------------+--------------------------------------+
| :code:`KICKED`          | Kicked member by administrators      |
+-------------------------+--------------------------------------+

Statuses can be extended with `is_member` flag by prefixing with
:code:`+` (for :code:`is_member == True)` or :code:`-` (for :code:`is_member == False`) symbol,
like :code:`+RESTRICTED` or :code:`-RESTRICTED`

Status groups
=============

The particular statuses can be combined via bitwise :code:`or` operator, like :code:`CREATOR | ADMINISTRATOR`

+-------------------------+-----------------------------------------------------------------------------------+
| name                    | Description                                                                       |
+=========================+===================================================================================+
| :code:`IS_MEMBER`       | Combination of :code:`(CREATOR | ADMINISTRATOR | MEMBER | +RESTRICTED)` statuses. |
+-------------------------+-----------------------------------------------------------------------------------+
| :code:`IS_ADMIN`        | Combination of :code:`(CREATOR | ADMINISTRATOR)` statuses.                        |
+-------------------------+-----------------------------------------------------------------------------------+
| :code:`IS_NOT_MEMBER`   | Combination of :code:`(LEFT | KICKED | -RESTRICTED)` statuses.                    |
+-------------------------+-----------------------------------------------------------------------------------+

Transitions
===========

Transitions can be defined via bitwise shift operators :code:`>>` and :code:`<<`.
Old chat member status should be defined in the left side for :code:`>>` operator (right side for :code:`<<`)
and new status should be specified on the right side for :code:`>>` operator (left side for :code:`<<`)

The direction of transition can be changed via bitwise inversion operator: :code:`~JOIN_TRANSITION`
will produce swap of old and new statuses.

+-----------------------------+-----------------------------------------------------------------------+
| name                        | Description                                                           |
+=============================+=======================================================================+
| :code:`JOIN_TRANSITION`     | Means status changed from :code:`IS_NOT_MEMBER` to :code:`IS_MEMBER`  |
|                             | (:code:`IS_NOT_MEMBER >> IS_MEMBER`)                                  |
+-----------------------------+-----------------------------------------------------------------------+
| :code:`LEAVE_TRANSITION`    | Means status changed from :code:`IS_MEMBER` to :code:`IS_NOT_MEMBER`  |
|                             | (:code:`~JOIN_TRANSITION`)                                            |
+-----------------------------+-----------------------------------------------------------------------+
| :code:`PROMOTED_TRANSITION` | Means status changed from                                             |
|                             | :code:`(MEMBER | RESTRICTED | LEFT | KICKED) >> ADMINISTRATOR`        |
|                             | (:code:`(MEMBER | RESTRICTED | LEFT | KICKED) >> ADMINISTRATOR`)      |
+-----------------------------+-----------------------------------------------------------------------+

.. note::

    Note that if you define the status unions (via :code:`|`) you will need to add brackets for the statement
    before use shift operator in due to operator priorities.


Allowed handlers
================

Allowed update types for this filter:

- `my_chat_member`
- `chat_member`
