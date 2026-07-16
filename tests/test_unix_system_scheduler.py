import unittest
from datetime import datetime

from app.core.service.schedule_service import (
    SCHEDULE_DAILY,
    SCHEDULE_MONTHLY,
    SCHEDULE_SINGLE,
    SCHEDULE_WEEKLY,
    ScheduleEntry,
)
from app.core.service.system_scheduler.cron_expr import (
    build_cron_schedule_lines,
    python_weekday_to_cron,
)
from app.core.service.system_scheduler.unix_common import (
    MFW_CRON_BEGIN,
    MFW_CRON_END,
    build_shell_job,
    mfw_cron_begin,
    mfw_cron_end,
    render_crontab,
    render_crontab_blocks,
    split_crontab,
    split_crontab_blocks,
)


class CronExpressionTests(unittest.TestCase):
    def _entry(self, schedule_type: str, params: dict) -> ScheduleEntry:
        return ScheduleEntry(
            entry_id="sched_test123",
            config_id="cfg_demo",
            name="Demo",
            schedule_type=schedule_type,
            params=params,
            force_start=False,
            enabled=True,
            created_at=datetime(2025, 6, 17, 8, 0, 0),
        )

    def test_python_weekday_to_cron(self) -> None:
        self.assertEqual(python_weekday_to_cron(0), 1)
        self.assertEqual(python_weekday_to_cron(6), 0)

    def test_single_schedule(self) -> None:
        lines = build_cron_schedule_lines(
            self._entry(SCHEDULE_SINGLE, {"run_at": "2025-06-18T09:30:00"})
        )
        self.assertEqual(lines, ["30 9 18 6 *"])

    def test_daily_schedule(self) -> None:
        lines = build_cron_schedule_lines(
            self._entry(
                SCHEDULE_DAILY,
                {
                    "start_at": "2025-06-17T08:00:00",
                    "hour": 8,
                    "minute": 0,
                    "interval_days": 1,
                },
            )
        )
        self.assertEqual(lines, ["0 8 * * *"])

    def test_weekly_schedule(self) -> None:
        lines = build_cron_schedule_lines(
            self._entry(
                SCHEDULE_WEEKLY,
                {
                    "start_at": "2025-06-17T08:00:00",
                    "hour": 8,
                    "minute": 0,
                    "interval_weeks": 1,
                    "weekdays": [0, 2, 4],
                },
            )
        )
        self.assertEqual(lines, ["0 8 * * 1,3,5"])

    def test_monthly_day_schedule(self) -> None:
        lines = build_cron_schedule_lines(
            self._entry(
                SCHEDULE_MONTHLY,
                {
                    "start_at": "2025-06-17T08:00:00",
                    "hour": 8,
                    "minute": 0,
                    "month": 6,
                    "month_day": 15,
                },
            )
        )
        self.assertEqual(lines, ["0 8 15 6 *"])

    def test_monthly_ordinal_schedule(self) -> None:
        lines = build_cron_schedule_lines(
            self._entry(
                SCHEDULE_MONTHLY,
                {
                    "start_at": "2025-06-17T08:00:00",
                    "hour": 8,
                    "minute": 0,
                    "month": 0,
                    "ordinal": 1,
                    "weekday": 2,
                },
            )
        )
        self.assertEqual(lines, ["0 8 8-14 * 3"])


class CrontabBlockTests(unittest.TestCase):
    def test_split_and_render_roundtrip(self) -> None:
        original = "\n".join(
            [
                "0 1 * * * /usr/bin/other",
                "",
                MFW_CRON_BEGIN,
                "# mfw-schedule:sched_a",
                "0 8 * * * /opt/MFW --config-id=a --direct-run",
                MFW_CRON_END,
                "5 6 * * * /usr/bin/another",
            ]
        ) + "\n"
        preserved, managed = split_crontab(original)
        self.assertEqual(preserved, ["0 1 * * * /usr/bin/other", "5 6 * * * /usr/bin/another"])
        self.assertEqual(
            managed["sched_a"],
            ["0 8 * * * /opt/MFW --config-id=a --direct-run"],
        )

        rendered = render_crontab(preserved, managed)
        preserved2, managed2 = split_crontab(rendered)
        self.assertEqual(preserved2, preserved)
        self.assertEqual(managed2, managed)

    def test_build_shell_job_quotes_paths(self) -> None:
        job = build_shell_job("cfg_demo", force_start=False)
        self.assertIn("--config-id=cfg_demo", job)
        self.assertIn("--direct-run", job)

    def test_build_shell_job_elevated_prefixed_sudo(self) -> None:
        job = build_shell_job("cfg_demo", force_start=False, run_elevated=True)
        self.assertTrue(job.startswith("sudo "), f"expected sudo prefix, got: {job}")
        self.assertIn("--config-id=cfg_demo", job)

    def test_split_preserves_other_instance_blocks(self) -> None:
        original = "\n".join(
            [
                "0 1 * * * /usr/bin/other",
                "",
                mfw_cron_begin("aaaaaaaa"),
                "# mfw-schedule:sched_a",
                "0 8 * * * /opt/MFW-a --config-id=a --direct-run",
                mfw_cron_end("aaaaaaaa"),
                mfw_cron_begin("bbbbbbbb"),
                "# mfw-schedule:sched_b",
                "0 9 * * * /opt/MFW-b --config-id=b --direct-run",
                mfw_cron_end("bbbbbbbb"),
            ]
        ) + "\n"
        preserved, blocks = split_crontab_blocks(original)
        self.assertEqual(preserved, ["0 1 * * * /usr/bin/other"])
        self.assertEqual(
            blocks["aaaaaaaa"]["sched_a"],
            ["0 8 * * * /opt/MFW-a --config-id=a --direct-run"],
        )
        self.assertEqual(
            blocks["bbbbbbbb"]["sched_b"],
            ["0 9 * * * /opt/MFW-b --config-id=b --direct-run"],
        )

        blocks["aaaaaaaa"] = {
            "sched_a2": ["0 10 * * * /opt/MFW-a2 --config-id=a2 --direct-run"]
        }
        rendered = render_crontab_blocks(preserved, blocks)
        preserved2, blocks2 = split_crontab_blocks(rendered)
        self.assertEqual(preserved2, preserved)
        self.assertNotIn("sched_a", blocks2["aaaaaaaa"])
        self.assertIn("sched_a2", blocks2["aaaaaaaa"])
        self.assertIn("sched_b", blocks2["bbbbbbbb"])


if __name__ == "__main__":
    unittest.main()
