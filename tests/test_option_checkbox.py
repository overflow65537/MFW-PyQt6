"""PI v2.10.1 checkbox min_count / max_count 测试。"""

from __future__ import annotations

import unittest

from app.core.utils.option_checkbox import (
    checkbox_selection_violation,
    clamp_checkbox_selection,
    collect_checkbox_violations,
    get_checkbox_limits,
    normalize_checkbox_selection,
)


def _match_option(**extra) -> dict:
    option = {
        "type": "checkbox",
        "label": "战斗划火柴",
        "cases": [
            {"name": "普通划火柴"},
            {"name": "蓄力划火柴"},
            {"name": "连续划火柴"},
        ],
    }
    option.update(extra)
    return option


class TestOptionCheckbox(unittest.TestCase):
    def test_default_limits(self):
        self.assertEqual((0, None), get_checkbox_limits(_match_option()))

    def test_limits_are_clamped_to_case_count(self):
        self.assertEqual((3, 3), get_checkbox_limits(_match_option(min_count=9, max_count=8)))

    def test_clamp_keeps_definition_order_and_max(self):
        option = _match_option(max_count=2)
        clamped = clamp_checkbox_selection(
            ["连续划火柴", "普通划火柴", "蓄力划火柴"], option
        )
        self.assertEqual(["普通划火柴", "蓄力划火柴"], clamped)

    def test_normalize_wrapped_value(self):
        self.assertEqual(
            ["普通划火柴", "蓄力划火柴"],
            normalize_checkbox_selection({"value": ["普通划火柴", "蓄力划火柴"]}),
        )

    def test_min_violation(self):
        option = _match_option(min_count=2)
        violation = checkbox_selection_violation(["普通划火柴"], option, "战斗划火柴")
        self.assertIsNotNone(violation)
        self.assertEqual("min", violation.kind)
        self.assertEqual(2, violation.min_count)

    def test_max_violation(self):
        option = _match_option(max_count=1)
        violation = checkbox_selection_violation(
            ["普通划火柴", "蓄力划火柴"], option, "战斗划火柴"
        )
        self.assertIsNotNone(violation)
        self.assertEqual("max", violation.kind)

    def test_collect_from_nested_resource_and_branches(self):
        interface_options = {
            "战斗划火柴": _match_option(min_count=1, max_count=2),
            "子功能": _match_option(min_count=1),
        }
        option_map = {
            "resource_options": {
                "战斗划火柴": {"value": []},
            },
            "setting_options": {
                "子功能": {"value": []},
            },
        }
        violations = collect_checkbox_violations(option_map, interface_options)
        kinds = {item.option_name: item.kind for item in violations}
        self.assertEqual("min", kinds["战斗划火柴"])
        self.assertEqual("min", kinds["子功能"])


if __name__ == "__main__":
    unittest.main()
