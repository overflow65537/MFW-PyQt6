import unittest

from app.core.runner.task_flow import (
    TaskFlowExecutionError,
    user_facing_error_already_shown,
)


class UserFacingErrorReportTests(unittest.TestCase):
    def test_same_error_text_is_already_shown(self):
        exc = TaskFlowExecutionError("Controller is missing")
        logs = [("INFO", "Starting", "00:00:01"), ("ERROR", "Controller is missing", "00:00:02")]
        self.assertTrue(user_facing_error_already_shown(exc, logs))

    def test_wrapped_copy_counts_as_shown(self):
        exc = TaskFlowExecutionError("Controller is missing")
        logs = [("ERROR", "Task flow error: Controller is missing", "00:00:02")]
        self.assertTrue(user_facing_error_already_shown(exc, logs))

    def test_flag_suppresses_a_differently_worded_wrapper(self):
        exc = TaskFlowExecutionError("资源加载失败", user_notified=True)
        logs = [("ERROR", "Resource package not found", "00:00:02")]
        self.assertTrue(user_facing_error_already_shown(exc, logs))

    def test_unseen_error_is_not_treated_as_shown(self):
        exc = RuntimeError("snapshot failed")
        logs = [("INFO", "Starting to load resources...", "00:00:01")]
        self.assertFalse(user_facing_error_already_shown(exc, logs))
