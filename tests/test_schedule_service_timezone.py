import unittest
from datetime import datetime, timedelta, timezone

from app.core.service.schedule_service import (
    SCHEDULE_DAILY,
    ScheduleEntry,
    ScheduleService,
    _parse_iso,
    _to_naive_local,
)


def _make_entry(
    entry_id: str,
    *,
    next_run: datetime | None = None,
    hour: int = 9,
    minute: int = 0,
) -> ScheduleEntry:
    return ScheduleEntry(
        entry_id=entry_id,
        config_id=f"cfg_{entry_id}",
        name=entry_id,
        schedule_type=SCHEDULE_DAILY,
        params={"interval_days": 1, "hour": hour, "minute": minute},
        force_start=False,
        enabled=True,
        created_at=datetime(2025, 6, 17, 8, 0, 0),
        next_run=next_run,
    )


def _make_service(entries: list[ScheduleEntry]) -> ScheduleService:
    """绕过 __init__ 的磁盘/计划任务扫描，只保留排序所需状态。"""
    service = ScheduleService.__new__(ScheduleService)
    service._schedules = list(entries)
    return service


class ParseIsoTimezoneTests(unittest.TestCase):
    def test_parses_dotnet_roundtrip_offset_as_naive_local(self) -> None:
        # Get-ScheduledTaskInfo 的 NextRunTime.ToString('o') 会带本机偏移量
        raw = "2025-06-18T09:30:00.0000000+08:00"
        parsed = _parse_iso(raw)

        self.assertIsNotNone(parsed)
        assert parsed is not None
        expected = datetime.fromisoformat(raw).astimezone().replace(tzinfo=None)
        self.assertIsNone(parsed.tzinfo)
        self.assertEqual(parsed, expected)

    def test_parses_utc_suffix_as_naive_local(self) -> None:
        parsed = _parse_iso("2025-06-18T01:30:00Z")

        self.assertIsNotNone(parsed)
        assert parsed is not None
        expected = datetime(2025, 6, 18, 1, 30, tzinfo=timezone.utc)
        self.assertIsNone(parsed.tzinfo)
        self.assertEqual(parsed, expected.astimezone().replace(tzinfo=None))

    def test_naive_iso_is_unchanged(self) -> None:
        self.assertEqual(
            _parse_iso("2025-06-18T09:30:00"), datetime(2025, 6, 18, 9, 30)
        )

    def test_invalid_or_empty_input_returns_none(self) -> None:
        self.assertIsNone(_parse_iso(None))
        self.assertIsNone(_parse_iso(""))
        self.assertIsNone(_parse_iso("not-a-datetime"))

    def test_to_naive_local_keeps_none_and_naive_values(self) -> None:
        self.assertIsNone(_to_naive_local(None))
        naive = datetime(2025, 6, 18, 9, 30)
        self.assertIs(_to_naive_local(naive), naive)


class ScheduleSortTimezoneTests(unittest.TestCase):
    def test_sort_mixes_aware_and_naive_next_run(self) -> None:
        aware_next = datetime(2025, 6, 20, 8, 0, tzinfo=timezone(timedelta(hours=8)))
        entries = [
            _make_entry("later", next_run=datetime(2025, 6, 21, 8, 0)),
            _make_entry("aware", next_run=aware_next),
            _make_entry("pending", next_run=None),
            _make_entry("earlier", next_run=datetime(2025, 6, 19, 8, 0)),
        ]

        service = _make_service(entries)
        service._sort_schedules()

        self.assertEqual(
            [entry.entry_id for entry in service._schedules],
            ["earlier", "aware", "later", "pending"],
        )

    def test_sort_compares_aware_values_on_absolute_time(self) -> None:
        entries = [
            _make_entry(
                "utc", next_run=datetime(2025, 6, 18, 2, 0, tzinfo=timezone.utc)
            ),
            _make_entry(
                "plus8",
                next_run=datetime(
                    2025, 6, 18, 9, 0, tzinfo=timezone(timedelta(hours=8))
                ),
            ),
        ]

        service = _make_service(entries)
        service._sort_schedules()

        # 09:00+08:00 == 01:00Z，早于 02:00Z
        self.assertEqual(
            [entry.entry_id for entry in service._schedules], ["plus8", "utc"]
        )

    def test_entry_roundtrip_drops_offset(self) -> None:
        entry = _make_entry("roundtrip")
        entry.next_run = _parse_iso("2025-06-18T09:30:00.0000000+08:00")

        restored = ScheduleEntry.from_dict(entry.to_dict())

        self.assertIsNone(restored.next_run.tzinfo if restored.next_run else None)
        self.assertEqual(restored.next_run, entry.next_run)


if __name__ == "__main__":
    unittest.main()
