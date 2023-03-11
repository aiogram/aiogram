import pytest

from aiogram.utils.backoff import Backoff, BackoffConfig

BACKOFF_CONFIG = BackoffConfig(min_delay=0.1, max_delay=1.0, factor=2.0, jitter=0.0)


class TestBackoffConfig:
    @pytest.mark.parametrize(
        "kwargs",
        [
            dict(min_delay=1.0, max_delay=1.0, factor=2.0, jitter=0.1),  # equals min and max
            dict(min_delay=1.0, max_delay=1.0, factor=1.0, jitter=0.1),  # factor == 1
            dict(min_delay=1.0, max_delay=2.0, factor=0.5, jitter=0.1),  # factor < 1
            dict(min_delay=2.0, max_delay=1.0, factor=2.0, jitter=0.1),  # min > max
        ],
    )
    def test_incorrect_post_init(self, kwargs):
        with pytest.raises(ValueError):
            BackoffConfig(**kwargs)

    @pytest.mark.parametrize(
        "kwargs",
        [dict(min_delay=1.0, max_delay=2.0, factor=1.2, jitter=0.1)],
    )
    def test_correct_post_init(self, kwargs):
        assert BackoffConfig(**kwargs)


class TestBackoff:
    def test_aliases(self):
        backoff = Backoff(config=BACKOFF_CONFIG)
        assert backoff.min_delay == BACKOFF_CONFIG.min_delay
        assert backoff.max_delay == BACKOFF_CONFIG.max_delay
        assert backoff.factor == BACKOFF_CONFIG.factor
        assert backoff.jitter == BACKOFF_CONFIG.jitter

    def test_calculation(self):
        backoff = Backoff(config=BACKOFF_CONFIG)
        index = 0

        iterable = iter(backoff)
        assert iterable == backoff

        assert backoff.current_delay == 0.0
        assert backoff.next_delay == 0.1

        while (val := next(backoff)) < 1:
            index += 1
            assert val in {0.1, 0.2, 0.4, 0.8}

        assert next(backoff) == 1
        assert next(backoff) == 1
        assert index == 4

        assert backoff.current_delay == 1
        assert backoff.next_delay == 1
        assert backoff.counter == 7  # 4+1 in while loop + 2 after loop

        assert str(backoff) == "Backoff(tryings=7, current_delay=1.0, next_delay=1.0)"

        backoff.reset()
        assert backoff.current_delay == 0.0
        assert backoff.next_delay == 0.1
        assert backoff.counter == 0

    def test_sleep(self):
        backoff = Backoff(config=BACKOFF_CONFIG)
        backoff.sleep()
        assert backoff.counter == 1

    async def test_asleep(self):
        backoff = Backoff(config=BACKOFF_CONFIG)
        await backoff.asleep()
        assert backoff.counter == 1
