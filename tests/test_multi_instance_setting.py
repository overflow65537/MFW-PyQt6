import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.common.config import cfg
from app.view.task_interface.components.list_tool_bar_widget import (
    ConfigListToolBarWidget,
)
from app.view.task_interface.components.list_widget import ConfigListWidget


class MultiInstanceSettingTests(unittest.TestCase):
    def test_multi_instance_defaults_to_disabled(self):
        self.assertFalse(cfg.multi_instance_enabled.defaultValue)

    def test_running_runtime_locks_configuration_list_when_disabled(self):
        harness = SimpleNamespace(
            _runtime_running=True,
            service_coordinator=SimpleNamespace(
                get_running_config_ids=lambda: ["config-a"]
            ),
            set_locked=Mock(),
        )

        with patch(
            "app.view.task_interface.components.list_tool_bar_widget.cfg.get",
            return_value=False,
        ):
            ConfigListToolBarWidget._refresh_runtime_lock(harness)

        harness.set_locked.assert_called_once_with(True)

    def test_running_runtime_does_not_lock_configuration_list_when_enabled(self):
        harness = SimpleNamespace(
            _runtime_running=True,
            service_coordinator=SimpleNamespace(
                get_running_config_ids=lambda: ["config-a"]
            ),
            set_locked=Mock(),
        )

        with patch(
            "app.view.task_interface.components.list_tool_bar_widget.cfg.get",
            return_value=True,
        ):
            ConfigListToolBarWidget._refresh_runtime_lock(harness)

        harness.set_locked.assert_called_once_with(False)

    def test_background_runtime_is_considered_when_active_config_is_idle(self):
        harness = SimpleNamespace(
            _runtime_running=False,
            service_coordinator=SimpleNamespace(
                get_running_config_ids=lambda: ["config-a"]
            ),
            set_locked=Mock(),
        )

        with patch(
            "app.view.task_interface.components.list_tool_bar_widget.cfg.get",
            return_value=False,
        ):
            ConfigListToolBarWidget._refresh_runtime_lock(harness)

        harness.set_locked.assert_called_once_with(True)

    def test_rejected_switch_restores_current_list_selection(self):
        select_current = Mock()
        harness = SimpleNamespace(
            _locked=False,
            service_coordinator=SimpleNamespace(
                select_config=Mock(return_value=False),
                configs=SimpleNamespace(current_config_id="config-a"),
            ),
            _select_config_by_id=select_current,
        )

        ConfigListWidget._on_item_selected_to_service(harness, "config-b")

        select_current.assert_called_once_with("config-a")

    def test_locked_list_ignores_user_selection_and_restores_current(self):
        select_config = Mock()
        select_current = Mock()
        harness = SimpleNamespace(
            _locked=True,
            service_coordinator=SimpleNamespace(
                select_config=select_config,
                configs=SimpleNamespace(current_config_id="config-a"),
            ),
            _select_config_by_id=select_current,
        )

        ConfigListWidget._on_item_selected_to_service(harness, "config-b")

        select_config.assert_not_called()
        select_current.assert_called_once_with("config-a")


if __name__ == "__main__":
    unittest.main()
