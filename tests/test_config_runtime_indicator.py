import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.view.task_interface.components.list_item import ConfigListItem
from app.view.task_interface.components.list_widget import ConfigListWidget


class ConfigRuntimeIndicatorTests(unittest.TestCase):
    def test_indicator_runs_for_active_runtime_states_and_stops_when_idle(self):
        indicator = Mock()
        item = SimpleNamespace(
            _runtime_state="idle",
            runtime_indicator=indicator,
        )

        ConfigListItem.set_runtime_state(item, "starting")
        ConfigListItem.set_runtime_state(item, "running")
        ConfigListItem.set_runtime_state(item, "stopping")

        indicator.show.assert_called()
        indicator.start.assert_called_once_with()
        indicator.stop.assert_not_called()

        ConfigListItem.set_runtime_state(item, "idle")

        indicator.stop.assert_called_once_with()
        indicator.hide.assert_called_once_with()

    def test_failed_runtime_hides_indicator(self):
        indicator = Mock()
        item = SimpleNamespace(
            _runtime_state="running",
            runtime_indicator=indicator,
        )

        ConfigListItem.set_runtime_state(item, "failed")

        indicator.stop.assert_called_once_with()
        indicator.hide.assert_called_once_with()

    def test_runtime_signal_updates_only_matching_configuration(self):
        class DummyConfigListItem:
            def __init__(self, config_id):
                self.item = SimpleNamespace(item_id=config_id)
                self.set_runtime_state = Mock()

        config_a = DummyConfigListItem("config-a")
        config_b = DummyConfigListItem("config-b")
        rows = [object(), object()]
        widgets = {
            rows[0]: config_a,
            rows[1]: config_b,
        }
        config_list = SimpleNamespace(
            count=lambda: len(rows),
            item=lambda index: rows[index],
            itemWidget=lambda row: widgets[row],
        )

        with patch(
            "app.view.task_interface.components.list_widget.ConfigListItem",
            DummyConfigListItem,
        ):
            ConfigListWidget._on_runtime_state_changed(
                config_list,
                "config-a",
                "running",
            )

        config_a.set_runtime_state.assert_called_once_with("running")
        config_b.set_runtime_state.assert_not_called()


if __name__ == "__main__":
    unittest.main()
