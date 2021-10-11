====================
Finite State Machine
====================

    A finite-state machine (FSM) or finite-state automaton (FSA, plural: automata), finite automaton,
    or simply a state machine, is a mathematical model of computation.

    It is an abstract machine that can be in exactly one of a finite number of states at any given time.
    The FSM can change from one state to another in response to some inputs;
    the change from one state to another is called a transition.

    An FSM is defined by a list of its states, its initial state,
    and the inputs that trigger each transition.

    .. raw:: html

        <hr>

    Source: `WikiPedia <wiki>`_

Usage example
=============

Not all functionality of the bot can be implemented as single handler,
for example you will need to collect some data from user in separated steps you will need to use FSM.


.. image:: ../../_static/fsm_example.png
    :alt: FSM Example

Let's see how to do that step-by-step

Step by step
------------

Before handle any states you will need to specify what kind of states you want to handle

.. literalinclude:: ../../../examples/finite_state_machine.py
    :language: python
    :linenos:
    :lineno-start: 15
    :lines: 15-18

And then write handler for each state separately from the start of dialog

Here is dialog can be started only via command :code:`/start`, so lets handle it and make transition user to state :code:`Form.name`

.. literalinclude:: ../../../examples/finite_state_machine.py
    :language: python
    :linenos:
    :lineno-start: 21
    :lines: 21-27

After that you will need to save some data to the storage and make transition to next step.

.. literalinclude:: ../../../examples/finite_state_machine.py
    :language: python
    :linenos:
    :lineno-start: 48
    :lines: 48-63

At the next steps user can make different answers, it can be `yes`, `no` or any other

Handle :code:`yes` and soon we need to handle :code:`Form.language` state

.. literalinclude:: ../../../examples/finite_state_machine.py
    :language: python
    :linenos:
    :lineno-start: 77
    :lines: 77-84

Handle :code:`no`

.. literalinclude:: ../../../examples/finite_state_machine.py
    :language: python
    :linenos:
    :lineno-start: 66
    :lines: 66-74

And handle any other answers

.. literalinclude:: ../../../examples/finite_state_machine.py
    :language: python
    :linenos:
    :lineno-start: 87
    :lines: 87-89

All possible cases of `like_bots` step was covered, let's implement finally step

.. literalinclude:: ../../../examples/finite_state_machine.py
    :language: python
    :linenos:
    :lineno-start: 92
    :lines: 92-102

And now you have covered all steps from the image, but you can make possibility to cancel conversation, lets do that via command or text

.. literalinclude:: ../../../examples/finite_state_machine.py
    :language: python
    :linenos:
    :lineno-start: 30
    :lines: 30-45

Complete example
----------------
.. literalinclude:: ../../../examples/finite_state_machine.py
    :language: python
    :linenos:


Read more
=========

.. toctree::

    storages


.. _wiki: https://en.wikipedia.org/wiki/Finite-state_machine
