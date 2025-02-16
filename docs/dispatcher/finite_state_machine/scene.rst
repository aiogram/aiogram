.. _Scenes:

=============
Scenes Wizard
=============

.. versionadded:: 3.2

.. warning::

    This feature is experimental and may be changed in future versions.

**aiogram's** basics API is easy to use and powerful,
allowing the implementation of simple interactions such as triggering a command or message
for a response.
However, certain tasks require a dialogue between the user and the bot.
This is where Scenes come into play.

Understanding Scenes
====================

A Scene in **aiogram** is like an abstract, isolated namespace or room that a user can be
ushered into via the code. When a user is within a Scene, most other global commands or
message handlers are bypassed, unless they are specifically designed to function outside of the Scenes.
This helps in creating an experience of focused interactions.
Scenes provide a structure for more complex interactions,
effectively isolating and managing contexts for different stages of the conversation.
They allow you to control and manage the flow of the conversation in a more organized manner.

Scene Lifecycle
---------------

Each Scene can be "entered", "left" or "exited", allowing for clear transitions between different
stages of the conversation.
For instance, in a multi-step form filling interaction, each step could be a Scene -
the bot guides the user from one Scene to the next as they provide the required information.

Scene Listeners
---------------

Scenes have their own hooks which are command or message listeners that only act while
the user is within the Scene.
These hooks react to user actions while the user is 'inside' the Scene,
providing the responses or actions appropriate for that context.
When the user is ushered from one Scene to another, the actions and responses change
accordingly as the user is now interacting with the set of listeners inside the new Scene.
These 'Scene-specific' hooks or listeners, detached from the global listening context,
allow for more streamlined and organized bot-user interactions.


Scene Interactions
------------------

Each Scene is like a self-contained world, with interactions defined within the scope of that Scene.
As such, only the handlers defined within the specific Scene will react to user's input during
the lifecycle of that Scene.


Scene Benefits
--------------

Scenes can help manage more complex interaction workflows and enable more interactive and dynamic
dialogs between the user and the bot.
This offers great flexibility in handling multi-step interactions or conversations with the users.

How to use Scenes
=================

For example we have a quiz bot, which asks the user a series of questions and then displays the results.

Lets start with the data models, in this example simple data models are used to represent
the questions and answers, in real life you would probably use a database to store the data.

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :lines: 25-101
    :caption: Questions list

Then, we need to create a Scene class that will represent the quiz game scene:

.. note::

    Keyword argument passed into class definition describes the scene name - is the same as state of the scene.

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :pyobject: QuizScene
    :emphasize-lines: 1
    :lines: -7
    :caption: Quiz Scene


Also we need to define a handler that helps to start the quiz game:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Start command handler
    :lines: 260-262

Once the scene is defined, we need to register it in the SceneRegistry:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :pyobject: create_dispatcher
    :caption: Registering the scene

So, now we can implement the quiz game logic, each question is sent to the user one by one,
and the user's answer is checked at the end of all questions.

Now we need to write an entry point for the question handler:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Question handler entry point
    :pyobject: QuizScene.on_enter


Once scene is entered, we should expect the user's answer, so we need to write a handler for it,
this handler should expect the text message, save the answer and retake
the question handler for the next question:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Answer handler
    :pyobject: QuizScene.answer

When user answer with unknown message, we should expect the text message again:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Unknown message handler
    :pyobject: QuizScene.unknown_message

When all questions are answered, we should show the results to the user, as you can see in the code below,
we use `await self.wizard.exit()` to exit from the scene when questions list is over in the `QuizScene.on_enter` handler.

Thats means that we need to write an exit handler to show the results to the user:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Show results handler
    :pyobject: QuizScene.on_exit

Also we can implement a actions to exit from the quiz game or go back to the previous question:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Exit handler
    :pyobject: QuizScene.exit

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Back handler
    :pyobject: QuizScene.back

Now we can run the bot and test the quiz game:

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Run the bot
    :lines: 291-

Complete them all

.. literalinclude:: ../../../examples/quiz_scene.py
    :language: python
    :caption: Quiz Example


Components
==========

- :class:`aiogram.fsm.scene.Scene` - represents a scene, contains handlers
- :class:`aiogram.fsm.scene.SceneRegistry` - container for all scenes in the bot, used to register scenes and resolve them by name
- :class:`aiogram.fsm.scene.ScenesManager` - manages scenes for each user, used to enter, leave and resolve current scene for user
- :class:`aiogram.fsm.scene.SceneConfig` - scene configuration, used to configure scene
- :class:`aiogram.fsm.scene.SceneWizard` - scene wizard, used to interact with user in scene from active scene handler
- Markers - marker for scene handlers, used to mark scene handlers


.. autoclass:: aiogram.fsm.scene.Scene
    :members:

.. autoclass:: aiogram.fsm.scene.SceneRegistry
    :members:

.. autoclass:: aiogram.fsm.scene.ScenesManager
    :members:

.. autoclass:: aiogram.fsm.scene.SceneConfig
    :members:

.. autoclass:: aiogram.fsm.scene.SceneWizard
    :members:

Markers
-------

Markers are similar to the Router event registering mechanism,
but they are used to mark scene handlers in the Scene class.

It can be imported from :code:`from aiogram.fsm.scene import on` and should be used as decorator.

Allowed event types:

- message
- edited_message
- channel_post
- edited_channel_post
- inline_query
- chosen_inline_result
- callback_query
- shipping_query
- pre_checkout_query
- poll
- poll_answer
- my_chat_member
- chat_member
- chat_join_request

Each event type can be filtered in the same way as in the Router.

Also each event type can be marked as scene entry point, exit point or leave point.

If you want to mark the scene can be entered from message or inline query,
you should use :code:`on.message` or :code:`on.inline_query` marker:

.. code-block:: python

    class MyScene(Scene, name="my_scene"):
        @on.message.enter()
        async def on_enter(self, message: types.Message):
            pass

        @on.callback_query.enter()
        async def on_enter(self, callback_query: types.CallbackQuery):
            pass


Scene has only three points for transitions:

- enter point - when user enters to the scene
- leave point - when user leaves the scene and the enter another scene
- exit point - when user exits from the scene
