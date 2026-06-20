from datetime import datetime

import pytest

from app.core.speedrun.conditions.cron import (
    DEFAULT_CRON_EXPRESSION,
    cron_matches,
    normalize_cron_expression,
)


pytestmark = pytest.mark.skipif(
    __import__("importlib").util.find_spec("croniter") is None,
    reason="croniter not installed",
)


def test_normalize_cron_expression_uses_default_for_empty():
    assert normalize_cron_expression("") == DEFAULT_CRON_EXPRESSION
    assert normalize_cron_expression("  0 8 * * *  ") == "0 8 * * *"


def test_daily_cron_matches_after_scheduled_time():
    assert cron_matches("0 9 * * *", datetime(2024, 1, 15, 10, 30)) is True


def test_daily_cron_does_not_match_before_scheduled_time():
    assert cron_matches("0 9 * * *", datetime(2024, 1, 15, 8, 30)) is False


def test_weekly_cron_matches_on_configured_weekday():
    # Monday = 1 in croniter (0=Sunday, 1=Monday)
    assert cron_matches("0 9 * * 1", datetime(2024, 1, 15, 10, 0)) is True


def test_weekly_cron_does_not_match_on_other_weekday():
    assert cron_matches("0 9 * * 1", datetime(2024, 1, 16, 10, 0)) is False


def test_invalid_cron_expression_does_not_match():
    assert cron_matches("not a cron", datetime(2024, 1, 15, 10, 0)) is False
