import unittest
from datetime import datetime
from unittest.mock import patch

from app.core.service.schedule_service import (
    SCHEDULE_DAILY,
    SCHEDULE_MONTHLY,
    SCHEDULE_SINGLE,
    SCHEDULE_WEEKLY,
    ScheduleEntry,
)
from app.core.service.system_scheduler.windows import (
    build_task_xml,
    task_folder,
    task_full_name,
)


class BuildTaskXmlTests(unittest.TestCase):
    def _entry(
        self,
        *,
        schedule_type: str,
        params: dict,
        force_start: bool = False,
        run_elevated: bool = False,
        enabled: bool = True,
    ) -> ScheduleEntry:
        return ScheduleEntry(
            entry_id="sched_test123",
            config_id="cfg_demo",
            name="Demo Config",
            schedule_type=schedule_type,
            params=params,
            force_start=force_start,
            run_elevated=run_elevated,
            enabled=enabled,
            created_at=datetime(2025, 6, 17, 8, 0, 0),
        )

    @patch(
        "app.core.service.system_scheduler.windows.resolve_schedule_launch_command",
        return_value=(r"C:\MFW\MFW.exe", "--config-id=cfg_demo --direct-run"),
    )
    def test_single_trigger_xml(self, _mock_command: object) -> None:
        xml = build_task_xml(
            self._entry(
                schedule_type=SCHEDULE_SINGLE,
                params={"run_at": "2025-06-18T09:30:00"},
            )
        )
        self.assertIn("<TimeTrigger>", xml)
        self.assertIn("<StartBoundary>2025-06-18T09:30:00</StartBoundary>", xml)
        self.assertIn("<MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>", xml)

    @patch(
        "app.core.service.system_scheduler.windows.resolve_schedule_launch_command",
        return_value=(r"C:\MFW\MFW.exe", "--config-id=cfg_demo --direct-run --force-restart"),
    )
    def test_force_start_uses_cli_arguments(self, mock_command: object) -> None:
        build_task_xml(
            self._entry(
                schedule_type=SCHEDULE_SINGLE,
                params={"run_at": "2025-06-18T09:30:00"},
                force_start=True,
            )
        )
        mock_command.assert_called_once_with("cfg_demo", force_start=True)

    @patch(
        "app.core.service.system_scheduler.windows.resolve_schedule_launch_command",
        return_value=(r"C:\MFW\MFW.exe", "--config-id=cfg_demo --direct-run"),
    )
    def test_daily_trigger_xml(self, _mock_command: object) -> None:
        xml = build_task_xml(
            self._entry(
                schedule_type=SCHEDULE_DAILY,
                params={
                    "start_at": "2025-06-17T08:00:00",
                    "hour": 8,
                    "minute": 0,
                    "interval_days": 2,
                },
            )
        )
        self.assertIn("<CalendarTrigger>", xml)
        self.assertIn("<ScheduleByDay>", xml)
        self.assertIn("<DaysInterval>2</DaysInterval>", xml)

    @patch(
        "app.core.service.system_scheduler.windows.resolve_schedule_launch_command",
        return_value=(r"C:\MFW\MFW.exe", "--config-id=cfg_demo --direct-run"),
    )
    def test_weekly_trigger_xml(self, _mock_command: object) -> None:
        xml = build_task_xml(
            self._entry(
                schedule_type=SCHEDULE_WEEKLY,
                params={
                    "start_at": "2025-06-17T08:00:00",
                    "hour": 8,
                    "minute": 0,
                    "interval_weeks": 1,
                    "weekdays": [0, 2, 4],
                },
            )
        )
        self.assertIn("<CalendarTrigger>", xml)
        self.assertIn("<ScheduleByWeek>", xml)
        self.assertIn("<Monday/>", xml)
        self.assertIn("<Wednesday/>", xml)
        self.assertIn("<Friday/>", xml)

    @patch(
        "app.core.service.system_scheduler.windows.resolve_schedule_launch_command",
        return_value=(r"C:\MFW\MFW.exe", "--config-id=cfg_demo --direct-run"),
    )
    def test_elevated_trigger_xml(self, _mock_command: object) -> None:
        xml = build_task_xml(
            self._entry(
                schedule_type=SCHEDULE_SINGLE,
                params={"run_at": "2025-06-18T09:30:00"},
                run_elevated=True,
            )
        )
        self.assertIn("<RunLevel>HighestAvailable</RunLevel>", xml)

    @patch(
        "app.core.service.system_scheduler.windows.resolve_schedule_launch_command",
        return_value=(r"C:\MFW\MFW.exe", "--config-id=cfg_demo --direct-run"),
    )
    def test_non_elevated_trigger_xml(self, _mock_command: object) -> None:
        xml = build_task_xml(
            self._entry(
                schedule_type=SCHEDULE_SINGLE,
                params={"run_at": "2025-06-18T09:30:00"},
                run_elevated=False,
            )
        )
        self.assertNotIn("RunLevel", xml)

    @patch(
        "app.core.service.system_scheduler.windows.resolve_schedule_launch_command",
        return_value=(r"C:\MFW\MFW.exe", "--config-id=cfg_demo --direct-run"),
    )
    def test_monthly_dow_trigger_xml(self, _mock_command: object) -> None:
        xml = build_task_xml(
            self._entry(
                schedule_type=SCHEDULE_MONTHLY,
                params={
                    "start_at": "2025-06-17T08:00:00",
                    "hour": 8,
                    "minute": 0,
                    "month": 0,
                    "ordinal": 1,
                    "weekday": 2,
                },
            )
        )
        self.assertIn("<ScheduleByMonthDayOfWeek>", xml)
        self.assertIn("<Week>2</Week>", xml)
        self.assertIn("<Wednesday/>", xml)

    @patch(
        "app.core.service.system_scheduler.windows.resolve_schedule_task_folder",
        return_value="MFW-ChainFlow Assistant-testinst01",
    )
    def test_task_full_name(self, _mock_folder: object) -> None:
        self.assertEqual(
            task_full_name("sched_abc"),
            "\\MFW-ChainFlow Assistant-testinst01\\sched_abc",
        )
        self.assertEqual(task_folder(), "MFW-ChainFlow Assistant-testinst01")


if __name__ == "__main__":
    unittest.main()
