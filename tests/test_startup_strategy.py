import unittest

from app.utils.startup_strategy import (
    ExistingInstanceAction,
    ReuseExistingCommand,
    decide_existing_instance_action,
    decide_reuse_existing_command,
)


class ExistingInstanceStrategyTests(unittest.TestCase):
    def test_new_process_always_starts_when_no_instance_exists(self) -> None:
        for reuse_existing in (False, True):
            for force_restart in (False, True):
                with self.subTest(
                    reuse_existing=reuse_existing,
                    force_restart=force_restart,
                ):
                    self.assertEqual(
                        ExistingInstanceAction.START,
                        decide_existing_instance_action(
                            existing_instance=False,
                            reuse_existing=reuse_existing,
                            force_restart=force_restart,
                        ),
                    )

    def test_existing_instance_uses_compatibility_matrix(self) -> None:
        cases = (
            (False, False, ExistingInstanceAction.ACTIVATE),
            (False, True, ExistingInstanceAction.RESTART),
            (True, False, ExistingInstanceAction.REUSE),
            (True, True, ExistingInstanceAction.REUSE),
        )
        for reuse_existing, force_restart, expected in cases:
            with self.subTest(
                reuse_existing=reuse_existing,
                force_restart=force_restart,
            ):
                self.assertEqual(
                    expected,
                    decide_existing_instance_action(
                        existing_instance=True,
                        reuse_existing=reuse_existing,
                        force_restart=force_restart,
                    ),
                )

    def test_reuse_only_runs_when_direct_run_is_explicit(self) -> None:
        cases = (
            (False, None, ReuseExistingCommand.ACTIVATE),
            (False, "config-a", ReuseExistingCommand.SWITCH_CONFIG),
            (True, None, ReuseExistingCommand.RUN),
            (True, "config-a", ReuseExistingCommand.RUN),
        )
        for direct_run, config_id, expected in cases:
            with self.subTest(direct_run=direct_run, config_id=config_id):
                self.assertEqual(
                    expected,
                    decide_reuse_existing_command(
                        direct_run=direct_run,
                        config_id=config_id,
                    ),
                )


if __name__ == "__main__":
    unittest.main()
