import unittest

from app.utils.startup_strategy import (
    ExistingInstanceAction,
    decide_existing_instance_action,
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


if __name__ == "__main__":
    unittest.main()
