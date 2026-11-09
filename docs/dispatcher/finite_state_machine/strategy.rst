========
Strategy
========

This module provides the `FSMStrategy` enumeration which is used to define the strategy of the finite state machine.


.. autoclass:: aiogram.fsm.strategy.FSMStrategy
    :members:


Messages sent on behalf of a chat
---------------------------------

Messages of anonymous group administrators and of users posting as a channel carry a placeholder
user in :code:`from`, so by default all of them share one FSM state.
Pass :code:`fsm_key_on_sender_chat=True` to the :class:`~aiogram.dispatcher.dispatcher.Dispatcher`
to use :code:`sender_chat.id` as the user id of the FSM key for such messages in non-channel chats.
