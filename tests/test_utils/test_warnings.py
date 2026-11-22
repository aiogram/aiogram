from aiogram.utils.warnings import AiogramWarning


def test_aiogram_warning_is_a_warning():
    # The base class AG4048 points to now that Recommendation is gone
    assert issubclass(AiogramWarning, Warning)
