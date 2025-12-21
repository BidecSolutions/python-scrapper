from datetime import datetime, timezone, timedelta

from app.api.background_job_executor import _duration_seconds


def test_duration_handles_naive_and_aware_datetimes():
    started_naive = datetime(2025, 1, 1, 12, 0, 0)  # naive
    completed_aware = datetime(2025, 1, 1, 12, 0, 10, tzinfo=timezone.utc)

    duration = _duration_seconds(started_naive, completed_aware)

    assert duration == 10


def test_duration_handles_both_aware_datetimes():
    started = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    completed = started + timedelta(seconds=42)

    duration = _duration_seconds(started, completed)

    assert duration == 42


def test_duration_returns_none_when_missing_datetimes():
    assert _duration_seconds(None, None) is None
    assert _duration_seconds(datetime.now(), None) is None
