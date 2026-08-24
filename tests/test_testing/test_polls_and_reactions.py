import pytest

from aiogram.exceptions import TelegramBadRequest
from aiogram.test.world import PollState, WorldLookupError
from aiogram.types import ReactionTypeEmoji

THUMBS_UP = ReactionTypeEmoji(emoji="👍")
HEART = ReactionTypeEmoji(emoji="❤")


async def send_poll(env, chat, *, anonymous=False, **kwargs):
    return await env.bot.send_poll(
        chat_id=chat.id,
        question="Tabs or spaces?",
        options=["Tabs", "Spaces"],
        is_anonymous=anonymous,
        **kwargs,
    )


class TestPollState:
    def test_counts_are_derived_from_the_voters(self):
        poll = PollState(id="1", question="Q", options=["a", "b"])
        poll.votes = {7: [0], 8: [1], 9: [1]}

        assert [option.voter_count for option in poll.as_poll().options] == [1, 2]
        assert poll.as_poll().total_voter_count == 3

    def test_a_retraction_lowers_the_count(self):
        poll = PollState(id="1", question="Q", options=["a", "b"])
        poll.votes = {7: [0], 8: [0]}

        poll.votes.pop(7)

        assert poll.as_poll().options[0].voter_count == 1

    def test_an_unknown_poll_id_fails(self, env):
        with pytest.raises(WorldLookupError, match="not known to this environment"):
            env.world.poll("nope")


class TestSendingPolls:
    async def test_a_sent_poll_is_stored_on_its_message(self, env, private):
        message = await send_poll(env, private)

        assert message.poll is not None
        assert message.poll.question == "Tabs or spaces?"
        assert private.messages[-1].message_id == message.message_id
        assert message.poll.id in env.world.polls

    async def test_poll_options_carry_their_text(self, env, private):
        message = await send_poll(env, private)

        assert [option.text for option in message.poll.options] == ["Tabs", "Spaces"]

    async def test_a_quiz_keeps_its_answer(self, env, private):
        message = await send_poll(env, private, type="quiz", correct_option_id=1)

        assert message.poll.type == "quiz"
        assert message.poll.correct_option_id == 1


class TestVoting:
    async def test_a_vote_reaches_the_handler_and_the_poll(self, env, private, alice):
        message = await send_poll(env, private)
        seen = []
        env.dispatcher.poll_answer.register(lambda answer: seen.append(answer.option_ids))

        await alice.vote(message.poll.id, [1])

        assert seen == [[1]]
        assert env.world.poll(message.poll.id).vote_count(1) == 1

    async def test_counts_stay_consistent_across_voters_and_a_retraction(
        self,
        env,
        private,
        alice,
    ):
        message = await send_poll(env, private)
        poll_id = message.poll.id
        poll = env.world.poll(poll_id)
        poll.votes[999] = [0]
        poll.votes[998] = [1]

        await alice.vote(poll_id, [1])
        await alice.vote(poll_id, [])

        rebuilt = poll.as_poll()
        assert [option.voter_count for option in rebuilt.options] == [1, 1]
        assert rebuilt.total_voter_count == len(poll.votes)

    async def test_voting_in_a_closed_poll_fails(self, env, private, alice):
        message = await send_poll(env, private)
        await env.bot.stop_poll(chat_id=private.id, message_id=message.message_id)

        with pytest.raises(WorldLookupError, match="is closed"):
            await alice.vote(message.poll.id, [0])

    async def test_voting_in_an_anonymous_poll_is_refused(self, env, private, alice):
        """Telegram never delivers a poll_answer for an anonymous poll."""
        message = await send_poll(env, private, anonymous=True)

        with pytest.raises(WorldLookupError, match="anonymous"):
            await alice.vote(message.poll.id, [0])

    async def test_an_anonymous_poll_delivers_the_aggregate_update(self, env, private, alice):
        message = await send_poll(env, private, anonymous=True)
        seen = []
        env.dispatcher.poll.register(lambda poll: seen.append(poll.id))

        await alice.poll_update(message.poll.id)

        assert seen == [message.poll.id]

    async def test_voting_still_works_after_the_message_is_deleted(self, env, private, alice):
        message = await send_poll(env, private)
        await env.bot.delete_message(chat_id=private.id, message_id=message.message_id)

        await alice.vote(message.poll.id, [0])

        assert env.world.poll(message.poll.id).vote_count(0) == 1


class TestStoppingPolls:
    async def test_stopping_returns_the_poll_that_was_sent(self, env, private, alice):
        message = await send_poll(env, private)
        await alice.vote(message.poll.id, [1])

        stopped = await env.bot.stop_poll(chat_id=private.id, message_id=message.message_id)

        assert stopped.id == message.poll.id
        assert stopped.is_closed is True
        assert stopped.options[1].voter_count == 1

    async def test_the_stored_message_reflects_the_closed_poll(self, env, private):
        message = await send_poll(env, private)

        await env.bot.stop_poll(chat_id=private.id, message_id=message.message_id)

        assert private.messages[-1].poll.is_closed is True

    async def test_stopping_twice_fails(self, env, private):
        message = await send_poll(env, private)
        await env.bot.stop_poll(chat_id=private.id, message_id=message.message_id)

        with pytest.raises(TelegramBadRequest, match="already been closed"):
            await env.bot.stop_poll(chat_id=private.id, message_id=message.message_id)

    async def test_stopping_a_message_with_no_poll_fails(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        with pytest.raises(TelegramBadRequest, match="doesn't contain a poll"):
            await env.bot.stop_poll(chat_id=private.id, message_id=message.message_id)

    async def test_stopping_an_unknown_message_fails(self, env, private):
        with pytest.raises(TelegramBadRequest, match="message to edit not found"):
            await env.bot.stop_poll(chat_id=private.id, message_id=999)


class TestBotReactions:
    async def test_the_bot_reacts_to_a_message(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        await env.bot.set_message_reaction(
            chat_id=private.id,
            message_id=message.message_id,
            reaction=[THUMBS_UP],
        )

        assert private.reactions_for(message.message_id) == {env.world.bot_user.id: [THUMBS_UP]}

    async def test_reacting_again_replaces_the_previous_reaction(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        await env.bot.set_message_reaction(
            chat_id=private.id,
            message_id=message.message_id,
            reaction=[THUMBS_UP],
        )

        await env.bot.set_message_reaction(
            chat_id=private.id,
            message_id=message.message_id,
            reaction=[HEART],
        )

        assert private.reactions_for(message.message_id)[env.world.bot_user.id] == [HEART]

    async def test_an_empty_reaction_removes_the_bots(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        await env.bot.set_message_reaction(
            chat_id=private.id,
            message_id=message.message_id,
            reaction=[THUMBS_UP],
        )

        await env.bot.set_message_reaction(chat_id=private.id, message_id=message.message_id)

        assert private.reactions_for(message.message_id) == {}

    async def test_reacting_to_an_unknown_message_fails(self, env, private):
        with pytest.raises(TelegramBadRequest, match="message to react to not found"):
            await env.bot.set_message_reaction(
                chat_id=private.id,
                message_id=999,
                reaction=[THUMBS_UP],
            )


class TestReactionCounts:
    async def test_counts_aggregate_across_reactors(self, env, private, alice):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        await alice.react(message, "👍")
        private.set_reaction(message.message_id, 999, [THUMBS_UP])
        await env.bot.set_message_reaction(
            chat_id=private.id,
            message_id=message.message_id,
            reaction=[HEART],
        )

        counts = {
            item.type.emoji: item.total_count
            for item in private.reaction_counts(message.message_id)
        }

        assert counts == {"👍": 2, "❤": 1}

    async def test_a_message_with_no_reactions_has_no_counts(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        assert private.reaction_counts(message.message_id) == []


class TestModeratingReactions:
    async def test_deleting_one_reaction_off_one_message(self, env, private, alice):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        await alice.react(message, "👍")
        private.set_reaction(message.message_id, 999, [HEART])

        await env.bot.delete_message_reaction(
            chat_id=private.id,
            message_id=message.message_id,
            user_id=alice.user.id,
        )

        assert private.reactions_for(message.message_id) == {999: [HEART]}

    async def test_deleting_all_of_one_actors_reactions_across_the_chat(
        self,
        env,
        private,
        alice,
    ):
        """`deleteAllMessageReactions` is chat-wide and per-actor, despite the name."""
        first = await env.bot.send_message(chat_id=private.id, text="one")
        second = await env.bot.send_message(chat_id=private.id, text="two")
        await alice.react(first, "👍")
        await alice.react(second, "👍")
        private.set_reaction(first.message_id, 999, [HEART])

        await env.bot.delete_all_message_reactions(chat_id=private.id, user_id=alice.user.id)

        assert private.reactions_for(first.message_id) == {999: [HEART]}
        assert private.reactions_for(second.message_id) == {}

    async def test_deleting_a_reaction_from_an_unknown_message_fails(self, env, private, alice):
        with pytest.raises(TelegramBadRequest, match="message to react to not found"):
            await env.bot.delete_message_reaction(
                chat_id=private.id,
                message_id=999,
                user_id=alice.user.id,
            )

    async def test_an_actor_chat_id_is_accepted_instead_of_a_user(self, env, private, team):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        private.set_reaction(message.message_id, team.id, [THUMBS_UP])

        await env.bot.delete_message_reaction(
            chat_id=private.id,
            message_id=message.message_id,
            actor_chat_id=team.id,
        )

        assert private.reactions_for(message.message_id) == {}

    async def test_naming_no_actor_changes_nothing(self, env, private, alice):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        await alice.react(message, "👍")

        await env.bot.delete_message_reaction(chat_id=private.id, message_id=message.message_id)
        await env.bot.delete_all_message_reactions(chat_id=private.id)

        assert private.reactions_for(message.message_id) == {alice.user.id: [THUMBS_UP]}


class TestReactionTriggers:
    async def test_changing_a_reaction_reports_the_previous_one(self, env, private, alice):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        def emojis(reactions):
            return [item.emoji for item in reactions]

        seen = []
        env.dispatcher.message_reaction.register(
            lambda event: seen.append((emojis(event.old_reaction), emojis(event.new_reaction))),
        )

        await alice.react(message, "👍")
        await alice.react(message, "❤")

        assert seen[0] == ([], ["👍"])
        assert seen[1] == (["👍"], ["❤"])

    async def test_removing_a_reaction(self, env, private, alice):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        await alice.react(message, "👍")
        seen = []
        env.dispatcher.message_reaction.register(lambda event: seen.append(event.new_reaction))

        await alice.react(message)

        assert seen == [[]]
        assert private.reactions_for(message.message_id) == {}

    async def test_reacting_by_message_id(self, env, private, alice):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        await alice.react(message.message_id, "👍")

        assert private.reactions_for(message.message_id) == {alice.user.id: [THUMBS_UP]}

    async def test_reacting_with_explicit_reaction_types(self, env, private, alice):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        await alice.react(message, [HEART])

        assert private.reactions_for(message.message_id) == {alice.user.id: [HEART]}

    async def test_reacting_to_an_unknown_message_fails(self, env, alice):
        with pytest.raises(WorldLookupError, match="does not exist"):
            await alice.react(999, "👍")

    async def test_the_aggregate_update_carries_the_counts(self, env, private, alice):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        await alice.react(message, "👍")
        seen = []
        env.dispatcher.message_reaction_count.register(
            lambda event: seen.append(event.reactions),
        )

        await alice.reaction_count(message)

        assert [item.type.emoji for item in seen[0]] == ["👍"]
