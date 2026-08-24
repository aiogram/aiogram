import pytest

from aiogram import Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment
from aiogram.test.modeling import GIFT_CATALOGUE, gift_catalogue

STAR_GIFT, STAR_GIFT_COST = GIFT_CATALOGUE[0]
HEART_GIFT, HEART_GIFT_COST = GIFT_CATALOGUE[1]


@pytest.fixture
def shop(dp):
    """A bot with stars to spend and a customer to spend them on."""
    blueprint = Blueprint()
    customer = blueprint.add_user("Customer")
    blueprint.add_private_chat(customer)
    blueprint.set_star_balance(1000)
    environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
    try:
        yield environment, environment.user(customer)
    finally:
        environment.dispose_sync()


async def charge_id_of(actor, **kwargs):
    """Pay, and return the charge id the handler would have received."""
    await actor.pay(**kwargs)
    return actor.chat.messages[-1].successful_payment.telegram_payment_charge_id


class TestTheLedger:
    async def test_a_declared_balance_needs_no_payment(self, shop):
        env, _ = shop

        assert (await env.bot.get_my_star_balance()).amount == 1000

    async def test_a_payment_credits_the_balance(self, shop):
        env, customer = shop

        await customer.pay("order-1", total_amount=250)

        assert (await env.bot.get_my_star_balance()).amount == 1250

    async def test_a_payment_appears_in_the_transactions(self, shop):
        env, customer = shop

        await customer.pay("order-1", total_amount=250)

        transactions = (await env.bot.get_star_transactions()).transactions
        assert [item.amount for item in transactions] == [250]

    async def test_a_non_star_payment_does_not_credit_stars(self, shop):
        env, customer = shop

        await customer.pay("order-1", currency="EUR", total_amount=500)

        assert (await env.bot.get_my_star_balance()).amount == 1000

    async def test_the_balance_always_equals_the_transactions(self, shop):
        """The invariant behind design decision D1 — derived, never stored."""
        env, customer = shop
        await customer.pay("a", total_amount=100)
        await customer.pay("b", total_amount=40)
        await env.bot.send_gift(gift_id=HEART_GIFT, user_id=customer.user.id)

        ledger = env.world.stars
        reported = (await env.bot.get_my_star_balance()).amount

        assert reported == ledger.opening_balance + sum(t.amount for t in ledger.transactions)
        assert reported == 1000 + 100 + 40 - HEART_GIFT_COST


class TestRefunds:
    async def test_refunding_restores_the_balance(self, shop):
        env, customer = shop
        charge = await charge_id_of(customer, invoice_payload="order-1", total_amount=250)
        assert (await env.bot.get_my_star_balance()).amount == 1250

        await env.bot.refund_star_payment(
            user_id=customer.user.id,
            telegram_payment_charge_id=charge,
        )

        assert (await env.bot.get_my_star_balance()).amount == 1000

    async def test_the_handler_can_refund_the_id_it_was_given(self, shop):
        """The point of recording charges: no fabricated identifiers anywhere."""
        env, customer = shop
        refunded = []

        async def on_payment(message, bot):
            charge = message.successful_payment.telegram_payment_charge_id
            await bot.refund_star_payment(
                user_id=message.from_user.id,
                telegram_payment_charge_id=charge,
            )
            refunded.append(charge)

        env.dispatcher.message.register(on_payment)

        await customer.pay("order-1", total_amount=250)

        assert len(refunded) == 1
        assert env.world.stars.charge(refunded[0]).is_refunded is True

    async def test_refunding_twice_fails(self, shop):
        env, customer = shop
        charge = await charge_id_of(customer, invoice_payload="order-1")
        await env.bot.refund_star_payment(
            user_id=customer.user.id,
            telegram_payment_charge_id=charge,
        )

        with pytest.raises(TelegramBadRequest, match="already been refunded"):
            await env.bot.refund_star_payment(
                user_id=customer.user.id,
                telegram_payment_charge_id=charge,
            )

    async def test_refunding_a_fabricated_charge_fails(self, shop):
        env, customer = shop

        with pytest.raises(TelegramBadRequest, match="No star payment with charge id"):
            await env.bot.refund_star_payment(
                user_id=customer.user.id,
                telegram_payment_charge_id="never-happened",
            )


class TestSubscriptions:
    async def test_cancelling_and_re_enabling(self, shop):
        env, customer = shop
        charge = await charge_id_of(customer, invoice_payload="sub-1", is_subscription=True)

        await env.bot.edit_user_star_subscription(
            user_id=customer.user.id,
            telegram_payment_charge_id=charge,
            is_canceled=True,
        )
        assert env.world.stars.charge(charge).is_subscription_canceled is True

        await env.bot.edit_user_star_subscription(
            user_id=customer.user.id,
            telegram_payment_charge_id=charge,
            is_canceled=False,
        )
        assert env.world.stars.charge(charge).is_subscription_canceled is False

    async def test_a_subscription_payment_is_marked_recurring(self, shop):
        env, customer = shop

        await customer.pay("sub-1", is_subscription=True)

        assert customer.chat.messages[-1].successful_payment.is_recurring is True

    async def test_editing_an_unknown_subscription_fails(self, shop):
        env, customer = shop

        with pytest.raises(TelegramBadRequest, match="No star payment with charge id"):
            await env.bot.edit_user_star_subscription(
                user_id=customer.user.id,
                telegram_payment_charge_id="never-happened",
                is_canceled=True,
            )


class TestTheCatalogue:
    async def test_the_catalogue_is_stable(self, shop):
        env, _ = shop

        first = await env.bot.get_available_gifts()
        second = await env.bot.get_available_gifts()

        assert [gift.id for gift in first.gifts] == [gift.id for gift in second.gifts]

    async def test_a_test_can_pick_a_gift_deterministically(self, shop):
        env, _ = shop

        gifts = (await env.bot.get_available_gifts()).gifts

        assert gifts[0].id == STAR_GIFT
        assert gifts[0].star_count == STAR_GIFT_COST

    def test_the_catalogue_is_identical_across_environments(self):
        assert [gift.id for gift in gift_catalogue()] == [gift.id for gift in gift_catalogue()]


class TestSendingGifts:
    async def test_sending_creates_owned_inventory_and_spends(self, shop):
        env, customer = shop

        await env.bot.send_gift(gift_id=HEART_GIFT, user_id=customer.user.id)

        owned = await env.bot.get_user_gifts(user_id=customer.user.id)
        assert owned.total_count == 1
        assert owned.gifts[0].gift.id == HEART_GIFT
        assert (await env.bot.get_my_star_balance()).amount == 1000 - HEART_GIFT_COST

    async def test_sending_to_a_chat(self, shop, dp):
        env, customer = shop
        chat = env.world.chats[customer.user.id]

        await env.bot.send_gift(gift_id=STAR_GIFT, chat_id=chat.id)

        assert (await env.bot.get_chat_gifts(chat_id=chat.id)).total_count == 1

    async def test_a_gift_outside_the_catalogue_fails(self, shop):
        env, customer = shop

        with pytest.raises(TelegramBadRequest, match="not in the catalogue"):
            await env.bot.send_gift(gift_id="gift-unicorn", user_id=customer.user.id)

    async def test_sending_without_a_recipient_fails(self, shop):
        env, _ = shop

        with pytest.raises(TelegramBadRequest, match="needs a user_id or a chat_id"):
            await env.bot.send_gift(gift_id=STAR_GIFT)

    async def test_an_unaffordable_gift_drives_the_balance_negative(self, dp):
        """Deliberate: a negative balance is visible, a silent rejection is not (D6)."""
        blueprint = Blueprint()
        customer = blueprint.add_user("Customer")
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            await env.bot.send_gift(gift_id=HEART_GIFT, user_id=customer.id)

            assert (await env.bot.get_my_star_balance()).amount == -HEART_GIFT_COST
        finally:
            env.dispose_sync()


class TestMovingGifts:
    @pytest.fixture
    async def owned(self, shop):
        env, customer = shop
        await env.bot.send_gift(gift_id=HEART_GIFT, user_id=customer.user.id)
        gift = next(iter(env.world.owned_gifts.values()))
        return env, customer, gift

    async def test_converting_returns_the_stars(self, owned):
        env, _, gift = owned
        before = (await env.bot.get_my_star_balance()).amount

        await env.bot.convert_gift_to_stars(
            business_connection_id="bc",
            owned_gift_id=gift.owned_gift_id,
        )

        assert (await env.bot.get_my_star_balance()).amount == before + HEART_GIFT_COST
        assert gift.owned_gift_id not in env.world.owned_gifts

    async def test_upgrading_marks_it_unique_and_spends(self, owned):
        env, customer, gift = owned
        before = (await env.bot.get_my_star_balance()).amount

        await env.bot.upgrade_gift(
            business_connection_id="bc",
            owned_gift_id=gift.owned_gift_id,
            star_count=20,
        )

        assert env.world.owned_gift(gift.owned_gift_id).is_unique is True
        assert (await env.bot.get_my_star_balance()).amount == before - 20
        owned_gifts = await env.bot.get_user_gifts(user_id=customer.user.id)
        assert owned_gifts.gifts[0].type == "unique"

    async def test_upgrading_without_payment_spends_nothing(self, owned):
        env, _, gift = owned
        before = (await env.bot.get_my_star_balance()).amount

        await env.bot.upgrade_gift(business_connection_id="bc", owned_gift_id=gift.owned_gift_id)

        assert (await env.bot.get_my_star_balance()).amount == before

    async def test_transferring_moves_ownership(self, owned):
        env, customer, gift = owned
        recipient = 987654

        await env.bot.transfer_gift(
            business_connection_id="bc",
            owned_gift_id=gift.owned_gift_id,
            new_owner_chat_id=recipient,
        )

        assert (await env.bot.get_user_gifts(user_id=customer.user.id)).total_count == 0
        assert (await env.bot.get_user_gifts(user_id=recipient)).total_count == 1

    async def test_a_paid_transfer_spends(self, owned):
        env, _, gift = owned
        before = (await env.bot.get_my_star_balance()).amount

        await env.bot.transfer_gift(
            business_connection_id="bc",
            owned_gift_id=gift.owned_gift_id,
            new_owner_chat_id=987654,
            star_count=30,
        )

        assert (await env.bot.get_my_star_balance()).amount == before - 30

    @pytest.mark.parametrize(
        ("method_name", "kwargs"),
        [
            ("convert_gift_to_stars", {}),
            ("upgrade_gift", {}),
            ("transfer_gift", {"new_owner_chat_id": 1}),
        ],
    )
    async def test_acting_on_an_unowned_gift_fails(self, shop, method_name, kwargs):
        env, _ = shop

        with pytest.raises(TelegramBadRequest, match="not owned by anybody"):
            await getattr(env.bot, method_name)(
                business_connection_id="bc",
                owned_gift_id="nobody-owns-this",
                **kwargs,
            )


class TestDeclaredGifts:
    async def test_a_declared_gift_is_readable(self, dp):
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        blueprint.add_owned_gift(owner, HEART_GIFT, star_count=HEART_GIFT_COST)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            owned = await env.bot.get_user_gifts(user_id=owner.id)

            assert owned.total_count == 1
            assert owned.gifts[0].gift.id == HEART_GIFT
        finally:
            env.dispose_sync()

    async def test_gifts_are_isolated_between_environments(self, dp):
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        gift = blueprint.add_owned_gift(owner)

        first = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        second = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        try:
            await first.bot.convert_gift_to_stars(
                business_connection_id="bc",
                owned_gift_id=gift.owned_gift_id,
            )

            assert (await second.bot.get_user_gifts(user_id=owner.id)).total_count == 1
        finally:
            first.dispose_sync()
            second.dispose_sync()


class TestBusinessAccountStars:
    @pytest.fixture
    def business(self, dp):
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        blueprint.add_private_chat(owner)
        connection = blueprint.add_business_connection(owner)
        blueprint.set_star_balance(500)
        blueprint.add_owned_gift(owner)
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield environment, connection
        finally:
            environment.dispose_sync()

    async def test_the_business_balance_is_readable(self, business):
        env, connection = business

        result = await env.bot.get_business_account_star_balance(
            business_connection_id=connection.id,
        )

        assert result.amount == 500

    async def test_business_gifts_are_the_owners_gifts(self, business):
        env, connection = business

        assert (
            await env.bot.get_business_account_gifts(business_connection_id=connection.id)
        ).total_count == 1

    async def test_transferring_business_stars_spends(self, business):
        env, connection = business

        await env.bot.transfer_business_account_stars(
            business_connection_id=connection.id,
            star_count=100,
        )

        assert (await env.bot.get_my_star_balance()).amount == 400

    @pytest.mark.parametrize(
        ("method_name", "kwargs"),
        [
            ("get_business_account_star_balance", {}),
            ("get_business_account_gifts", {}),
            ("transfer_business_account_stars", {"star_count": 1}),
        ],
    )
    async def test_an_unknown_connection_fails(self, business, method_name, kwargs):
        env, _ = business

        with pytest.raises(TelegramBadRequest, match="business connection"):
            await getattr(env.bot, method_name)(business_connection_id="missing", **kwargs)


class TestPremiumAndRights:
    async def test_gifting_premium_spends(self, shop):
        env, customer = shop

        await env.bot.gift_premium_subscription(
            user_id=customer.user.id,
            month_count=3,
            star_count=200,
        )

        assert (await env.bot.get_my_star_balance()).amount == 800

    async def test_rights_are_not_enforced(self, dp):
        """Consistent with the toolkit enforcing no rights anywhere."""
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        connection = blueprint.add_business_connection(owner, rights=None)
        gift = blueprint.add_owned_gift(owner)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            assert await env.bot.convert_gift_to_stars(
                business_connection_id=connection.id,
                owned_gift_id=gift.owned_gift_id,
            )
        finally:
            env.dispose_sync()
