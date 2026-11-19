"""
End-to-end proof that the toolkit drives the real framework.

Each test here exercises a feature of aiogram itself — FSM, Scenes, middlewares,
filters, callback flows — through the public toolkit API only.
"""

import pytest

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, SceneRegistry, on
from aiogram.fsm.state import State, StatesGroup
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.test import detach_router
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)


class Registration(StatesGroup):
    name = State()
    age = State()


class TestFsmFlow:
    @pytest.fixture(autouse=True)
    def _handlers(self, dp):
        @dp.message(Command("register"))
        async def start(message: Message, state: FSMContext):
            await state.set_state(Registration.name)
            await message.answer("What is your name?")

        @dp.message(Registration.name)
        async def got_name(message: Message, state: FSMContext):
            await state.update_data(name=message.text)
            await state.set_state(Registration.age)
            await message.answer(f"Nice to meet you, {message.text}. How old are you?")

        @dp.message(Registration.age, F.text.regexp(r"^\d+$"))
        async def got_age(message: Message, state: FSMContext):
            await state.update_data(age=int(message.text))
            data = await state.get_data()
            await state.clear()
            await message.answer(f"Registered {data['name']}, {data['age']}")

        @dp.message(Registration.age)
        async def bad_age(message: Message):
            await message.answer("Digits only, please")

    async def test_multi_step_conversation(self, env, alice, private, blueprint):
        await alice.send("/register")
        assert private.messages[-1].text == "What is your name?"

        await alice.send("Alice")
        assert "Nice to meet you, Alice" in private.messages[-1].text

        await alice.send("not a number")
        assert private.messages[-1].text == "Digits only, please"

        await alice.send("30")
        assert private.messages[-1].text == "Registered Alice, 30"

        state = env.state(blueprint.users[0], blueprint.chats[0])
        assert await state.get_state() is None

    async def test_state_can_be_arranged_to_skip_steps(self, env, alice, private, blueprint):
        state = env.state(blueprint.users[0], blueprint.chats[0])
        await state.set_state(Registration.age)
        await state.update_data(name="Bob")

        await alice.send("41")

        assert private.messages[-1].text == "Registered Bob, 41"


class Greeting(Scene, state="greeting"):
    @on.message.enter()
    async def entered(self, message: Message) -> None:
        await message.answer("Welcome to the scene")

    @on.message(F.text == "next")
    async def go_next(self, message: Message) -> None:
        await self.wizard.goto(Farewell)


class Farewell(Scene, state="farewell"):
    @on.message.enter()
    async def entered(self, message: Message, carried: str | None = None) -> None:
        await message.answer("Goodbye")


class TestSceneFlow:
    async def test_scene_entry_and_transition(self, env, dp, alice, private):
        registry = SceneRegistry(dp)
        registry.add(Greeting, Farewell)

        @dp.message(Command("scene"))
        async def enter(message: Message, scenes) -> None:
            await scenes.enter(Greeting)

        await alice.send("/scene")
        assert private.messages[-1].text == "Welcome to the scene"

        await alice.send("next")
        assert private.messages[-1].text == "Goodbye"

    async def test_scene_state_is_isolated_between_tests(self, env, dp, alice, blueprint):
        SceneRegistry(dp).add(Greeting, Farewell)

        state = env.state(blueprint.users[0], blueprint.chats[0])

        assert await state.get_state() is None


class TestMiddlewareAndFilters:
    async def test_middleware_data_reaches_handlers_and_filters(self, env, dp, alice, private):
        router = Router()

        @router.message.outer_middleware()
        async def inject(handler, event, data):
            data["role"] = "admin" if event.text.startswith("!") else "user"
            return await handler(event, data)

        @router.message(lambda message, role: role == "admin")
        async def admin_only(message: Message, role: str):
            await message.answer(f"hello {role}")

        @router.message()
        async def everyone(message: Message, role: str):
            await message.answer(f"denied for {role}")

        dp.include_router(router)

        await alice.send("!promote")
        assert private.messages[-1].text == "hello admin"

        await alice.send("promote")
        assert private.messages[-1].text == "denied for user"

    async def test_module_level_router_can_be_reused(self, env, dp, alice, private):
        shared = Router()

        @shared.message()
        async def handler(message: Message):
            await message.answer("from shared router")

        dp.include_router(shared)
        await alice.send("hi")
        assert private.messages[-1].text == "from shared router"

        # The second dispatcher would raise "Router is already attached" without this.
        from aiogram import Dispatcher

        other = Dispatcher()
        other.include_router(detach_router(shared))

        assert shared.parent_router is other


class TestCallbackFlow:
    async def test_keyboard_click_edits_the_message(self, env, dp, alice, private):
        @dp.message(Command("menu"))
        async def menu(message: Message):
            await message.answer(
                "Choose:",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="Yes", callback_data="answer:yes"),
                            InlineKeyboardButton(text="No", callback_data="answer:no"),
                        ],
                    ],
                ),
            )

        @dp.callback_query(F.data.startswith("answer:"))
        async def answered(query):
            choice = query.data.split(":")[1]
            await query.message.edit_text(f"You chose {choice}")
            await query.answer("Saved")

        await alice.send("/menu")
        assert private.messages[-1].reply_markup is not None

        await alice.click("answer:no")

        assert len(private.messages) == 2
        assert private.messages[-1].text == "You chose no"
        assert env.calls.last(AnswerCallbackQuery).text == "Saved"
        assert env.calls.count(SendMessage) == 1
