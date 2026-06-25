"""多实例模式下日志面板按 config_id 隔离缓冲的单元测试。

仅验证 LogoutputWidget 的数据层（缓冲/过滤/清空/切换）逻辑，
通过 __new__ 跳过重型 UI 构建，并对触及 UI 的方法打桩。
"""

import unittest

from app.view.task_interface.components.logoutput_widget import LogoutputWidget


class _StubLog(LogoutputWidget):
    """绕过 __init__，仅装配缓冲逻辑所需的最小状态与 UI 打桩。"""

    def __init__(self):  # noqa: D401 - 故意不调用父类 __init__
        self._config_log_records = {}
        self._current_log_config_id = "c_a"
        self._max_log_entries = 100
        self.rendered: list[tuple[str, str]] = []
        self.cleared = 0

    # --- UI 打桩 ---
    def add_structured_log(self, level, text):
        self.rendered.append((level, text))

    def _clear_display_only(self):
        self.cleared += 1
        self.rendered.clear()

    def _add_log_row(self, timestamp, text, level, capture_image=True):
        self.rendered.append((level, text))

    def _start_log_zip_attention_effect(self):
        pass

    def _normalize_level_by_text(self, level, text):
        return (level or "INFO").upper()


class MultiInstanceLogBufferTests(unittest.TestCase):
    def setUp(self) -> None:
        self.widget = _StubLog()

    def test_background_config_logs_are_buffered_not_rendered(self) -> None:
        # 当前显示 c_a；写入 c_b 的日志不应渲染，但应缓冲
        self.widget._on_log_output_at("c_b", "INFO", "hello-b")
        self.assertEqual(self.widget.rendered, [])
        self.assertEqual(
            [r[1] for r in self.widget._config_log_records["c_b"]], ["hello-b"]
        )

    def test_current_config_logs_render_and_buffer(self) -> None:
        self.widget._on_log_output_at("c_a", "INFO", "hello-a")
        self.assertEqual(self.widget.rendered, [("INFO", "hello-a")])
        self.assertIn("c_a", self.widget._config_log_records)

    def test_empty_config_id_attributes_to_current(self) -> None:
        self.widget._on_log_output_at("", "INFO", "current-log")
        self.assertEqual(
            [r[1] for r in self.widget._config_log_records["c_a"]], ["current-log"]
        )
        self.assertEqual(self.widget.rendered, [("INFO", "current-log")])

    def test_switch_config_rebuilds_from_target_buffer(self) -> None:
        self.widget._on_log_output_at("c_a", "INFO", "a1")
        self.widget._on_log_output_at("c_b", "INFO", "b1")
        self.widget._on_log_output_at("c_b", "INFO", "b2")
        self.widget.rendered.clear()

        self.widget._on_config_changed("c_b")
        self.assertEqual(self.widget._current_log_config_id, "c_b")
        self.assertEqual(
            [r[1] for r in self.widget.rendered], ["b1", "b2"]
        )

    def test_clear_requested_only_affects_target(self) -> None:
        self.widget._on_log_output_at("c_a", "INFO", "a1")
        self.widget._on_log_output_at("c_b", "INFO", "b1")

        self.widget._on_clear_requested_at("c_b")
        self.assertNotIn("c_b", self.widget._config_log_records)
        self.assertIn("c_a", self.widget._config_log_records)

    def test_logs_to_old_config_hidden_after_switch(self) -> None:
        """切换显示配置后，仍归属旧 config_id 的日志不应渲染（桥接未同步时的表现）。"""
        self.widget._on_config_changed("c_b")
        self.widget.rendered.clear()
        self.widget._on_log_output_at("c_a", "INFO", "stale-bridge-log")
        self.assertEqual(self.widget.rendered, [])
        self.assertIn("c_a", self.widget._config_log_records)

    def test_logs_render_when_config_id_matches_display(self) -> None:
        """桥接 config_id 与当前显示一致时，新日志应正常渲染。"""
        self.widget._on_config_changed("c_b")
        self.widget.rendered.clear()
        self.widget._on_log_output_at("c_b", "INFO", "b-visible")
        self.assertEqual(
            [r[1] for r in self.widget.rendered], ["b-visible"]
        )

    def test_buffer_respects_max_entries(self) -> None:
        from app.common.config import cfg

        try:
            cap = cfg.get(cfg.log_max_images)
        except Exception:
            cap = None
        if not isinstance(cap, int) or cap <= 0:
            cap = self.widget._max_log_entries

        for i in range(cap + 25):
            self.widget._record_log("c_x", "INFO", f"line-{i}", "00:00:00")
        records = self.widget._config_log_records["c_x"]
        self.assertEqual(len(records), cap)
        # 淘汰应保留最新的若干条
        self.assertEqual(records[-1][1], f"line-{cap + 24}")


if __name__ == "__main__":
    unittest.main()
