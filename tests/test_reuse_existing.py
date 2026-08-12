import unittest
from datetime import datetime

from app.core.service.schedule_service import ScheduleEntry
from mfw_cli import (
    FLAG_REUSE_EXISTING,
    StartupOptions,
    build_startup_argv,
    parse_startup_cli,
)


class ReuseExistingTests(unittest.TestCase):
    def test_cli_parses_reuse_existing(self) -> None:
        options, _, _ = parse_startup_cli(
            ["--config-id=cfg_demo", "--direct-run", FLAG_REUSE_EXISTING]
        )
        self.assertTrue(options.reuse_existing)
        self.assertEqual(options.config_id, "cfg_demo")

    def test_cli_serializes_reuse_existing(self) -> None:
        argv = build_startup_argv(
            StartupOptions(config_id="cfg_demo", reuse_existing=True)
        )
        self.assertIn(FLAG_REUSE_EXISTING, argv)

    def test_schedule_entry_defaults_reuse_existing_to_false(self) -> None:
        entry = ScheduleEntry.from_dict(
            {
                "entry_id": "sched_demo",
                "config_id": "cfg_demo",
                "force_start": False,
                "enabled": True,
                "created_at": datetime.now().isoformat(),
            }
        )
        self.assertFalse(entry.reuse_existing)

    def test_schedule_entry_serializes_reuse_existing(self) -> None:
        entry = ScheduleEntry(
            entry_id="sched_demo",
            config_id="cfg_demo",
            name="Demo",
            schedule_type="daily",
            params={},
            force_start=False,
            enabled=True,
            created_at=datetime.now(),
            reuse_existing=True,
        )
        self.assertTrue(entry.to_dict()["reuse_existing"])


if __name__ == "__main__":
    unittest.main()
