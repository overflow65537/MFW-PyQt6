"""pipeline_helper 单元测试（对齐 PI V2 option 协议）。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.common.constants import _RESOURCE_
from app.core.utils.pipeline_helper import (
    ChildKeyParser,
    LegacyChildKeyParser,
    _extract_option_value_and_children,
    get_controller_option_pipeline_override,
    get_pipeline_override_from_task_option,
)


def _base_interface() -> dict:
    """最小 PI V2 风格 interface fixture。"""
    return {
        "option": {
            "作战关卡": {
                "type": "select",
                "cases": [
                    {
                        "name": "3-9 厄险",
                        "pipeline_override": {
                            "EnterTheShow": {"next": "MainChapter_3"}
                        },
                    },
                    {
                        "name": "4-20 厄险",
                        "pipeline_override": {
                            "EnterTheShow": {"next": "MainChapter_4"}
                        },
                    },
                ],
            },
            "刷完全部体力": {
                "type": "switch",
                "cases": [
                    {"name": "Yes", "pipeline_override": {"FarmAll": {"enabled": True}}},
                    {"name": "No", "pipeline_override": {"FarmAll": {"enabled": False}}},
                ],
            },
            "战斗划火柴": {
                "type": "checkbox",
                "cases": [
                    {
                        "name": "普通划火柴",
                        "pipeline_override": {"NormalMatch": {"enabled": True}},
                    },
                    {
                        "name": "蓄力划火柴",
                        "pipeline_override": {"ChargedMatch": {"enabled": True}},
                    },
                    {
                        "name": "连续划火柴",
                        "pipeline_override": {
                            "ComboMatch": {"enabled": True},
                            "SharedNode": {"priority": 1},
                        },
                    },
                ],
            },
            "自定义关卡": {
                "type": "input",
                "inputs": [
                    {"name": "章节号", "pipeline_type": "string"},
                    {"name": "超时时间", "pipeline_type": "int"},
                ],
                "pipeline_override": {
                    "EnterTheShow": {
                        "next": "MainChapter_{章节号}",
                        "timeout": "{超时时间}",
                    }
                },
            },
            "往世乐土-真我刻印自选": {
                "type": "input",
                "inputs": [{"name": "真我刻印自选优先级_1", "pipeline_type": "string"}],
                "pipeline_override": {
                    "往世乐土-选刻印-真我刻印选择": {
                        "expected": ["{真我刻印自选优先级_1}"]
                    }
                },
            },
            "低阶柜台": {
                "type": "switch",
                "cases": [
                    {"name": "Yes", "pipeline_override": {"Parent": {"enabled": True}}},
                    {"name": "No", "pipeline_override": {"Parent": {"enabled": False}}},
                ],
            },
            "Yes": {
                "type": "select",
                "cases": [
                    {
                        "name": "误匹配",
                        "pipeline_override": {"BadNode": {"enabled": True}},
                    }
                ],
            },
            "金兔子": {
                "type": "input",
                "inputs": [{"name": "数量", "pipeline_type": "string"}],
                "pipeline_override": {"GoldRabbit": {"expected": ["{数量}"]}},
            },
            "全局选项": {
                "type": "select",
                "cases": [
                    {
                        "name": "默认",
                        "pipeline_override": {"Shared": {"level": "global"}},
                    }
                ],
            },
            "资源选项": {
                "type": "select",
                "cases": [
                    {
                        "name": "覆盖",
                        "pipeline_override": {"Shared": {"level": "resource"}},
                    }
                ],
            },
            "控制器选项": {
                "type": "select",
                "cases": [
                    {
                        "name": "ctrl",
                        "pipeline_override": {"CtrlNode": {"enabled": True}},
                    }
                ],
            },
        },
        "controller": [
            {
                "name": "Win32",
                "type": "Win32",
                "option": ["控制器选项"],
            }
        ],
    }


class TestChildKeyParser(unittest.TestCase):
    def test_new_format_returns_key_as_option_name(self):
        parser = ChildKeyParser()
        self.assertEqual("输入A级角色名", parser.extract_option_name("输入A级角色名"))

    def test_legacy_format_extracts_child_name(self):
        parser = LegacyChildKeyParser()
        key = "低阶柜台_child_Yes_金兔子(低阶柜台)_0"
        self.assertEqual("金兔子(低阶柜台)", parser.extract_option_name(key))

    def test_legacy_format_falls_back_to_new_format(self):
        parser = LegacyChildKeyParser()
        self.assertEqual("子选项名", parser.extract_option_name("子选项名"))


class TestExtractOptionValueAndChildren(unittest.TestCase):
    def setUp(self):
        self.options = _base_interface()["option"]

    def test_simple_string_value(self):
        actual, branches = _extract_option_value_and_children("3-9 厄险")
        self.assertEqual("3-9 厄险", actual)
        self.assertIsNone(branches)

    def test_input_plain_dict_preset_format(self):
        """PI preset：input 类型为 record<string, string>。"""
        payload = {"章节号": "4", "超时时间": "20000"}
        actual, branches = _extract_option_value_and_children(
            payload, self.options, "自定义关卡"
        )
        self.assertEqual(payload, actual)
        self.assertIsNone(branches)

    def test_input_wrapped_value_client_persist_format(self):
        """Client 持久化：{"value": {字段: 值}}。"""
        payload = {"value": {"真我刻印自选优先级_1": "刻印A|刻印B"}}
        actual, branches = _extract_option_value_and_children(
            payload, self.options, "往世乐土-真我刻印自选"
        )
        self.assertEqual({"真我刻印自选优先级_1": "刻印A|刻印B"}, actual)
        self.assertEqual({}, branches)

    def test_input_dict_value_does_not_log_error(self):
        payload = {"value": {"真我刻印自选优先级_1": "刻印A"}}
        with patch("app.core.utils.pipeline_helper.logger.error") as mock_error:
            _extract_option_value_and_children(
                payload, self.options, "往世乐土-真我刻印自选"
            )
        mock_error.assert_not_called()

    def test_select_dict_value_logs_error(self):
        payload = {"value": {"unexpected": "dict"}}
        with patch("app.core.utils.pipeline_helper.logger.error") as mock_error:
            _extract_option_value_and_children(
                payload, self.options, "作战关卡"
            )
        mock_error.assert_called_once()
        self.assertIn("选项 value 字段类型异常", mock_error.call_args[0][0])

    def test_switch_with_branches(self):
        payload = {
            "value": "Yes",
            "branches": {
                "Yes": {"金兔子": {"value": {"数量": "3"}}},
                "No": {"金兔子": {"value": {"数量": ""}, "hidden": True}},
            },
        }
        actual, branches = _extract_option_value_and_children(payload)
        self.assertEqual("Yes", actual)
        self.assertEqual(payload["branches"], branches)

    def test_legacy_children_field_is_accepted(self):
        payload = {
            "value": "No",
            "children": {"No": {"金兔子": {"value": {"数量": "1"}}}},
        }
        actual, branches = _extract_option_value_and_children(payload)
        self.assertEqual("No", actual)
        self.assertEqual(payload["children"], branches)


class TestGetPipelineOverrideFromTaskOption(unittest.TestCase):
    def setUp(self):
        self.interface = _base_interface()

    def test_select_preset_string_value(self):
        override = get_pipeline_override_from_task_option(
            self.interface, {"作战关卡": "3-9 厄险"}
        )
        self.assertEqual("MainChapter_3", override["EnterTheShow"]["next"])

    def test_switch_yes_no_case_insensitive(self):
        override = get_pipeline_override_from_task_option(
            self.interface, {"刷完全部体力": "yes"}
        )
        self.assertTrue(override["FarmAll"]["enabled"])

    def test_checkbox_merge_follows_cases_definition_order(self):
        """PI：checkbox 按 cases 定义顺序合并，与勾选顺序无关。"""
        override = get_pipeline_override_from_task_option(
            self.interface,
            {"战斗划火柴": ["连续划火柴", "普通划火柴", "蓄力划火柴"]},
        )
        self.assertTrue(override["NormalMatch"]["enabled"])
        self.assertTrue(override["ChargedMatch"]["enabled"])
        self.assertTrue(override["ComboMatch"]["enabled"])
        # SharedNode 来自 cases 中最后定义的「连续划火柴」
        self.assertEqual(1, override["SharedNode"]["priority"])

    def test_input_plain_dict_with_type_conversion(self):
        override = get_pipeline_override_from_task_option(
            self.interface,
            {"自定义关卡": {"章节号": "4", "超时时间": "20000"}},
        )
        self.assertEqual("MainChapter_4", override["EnterTheShow"]["next"])
        self.assertEqual(20000, override["EnterTheShow"]["timeout"])

    def test_input_wrapped_value_replaces_placeholder(self):
        override = get_pipeline_override_from_task_option(
            self.interface,
            {
                "往世乐土-真我刻印自选": {
                    "value": {"真我刻印自选优先级_1": "刻印A|刻印B"}
                }
            },
        )
        self.assertEqual(
            ["刻印A|刻印B"],
            override["往世乐土-选刻印-真我刻印选择"]["expected"],
        )

    def test_switch_branches_do_not_treat_branch_key_as_option_name(self):
        """分支键（如 Yes）与 option 同名时，仍应按 branches 分组递归。"""
        override = get_pipeline_override_from_task_option(
            self.interface,
            {
                "低阶柜台": {
                    "value": "Yes",
                    "branches": {
                        "Yes": {"金兔子": {"value": {"数量": "5"}}},
                        "No": {
                            "金兔子": {"value": {"数量": "9"}, "hidden": True},
                        },
                    },
                }
            },
        )
        self.assertTrue(override["Parent"]["enabled"])
        self.assertEqual(["5"], override["GoldRabbit"]["expected"])
        self.assertNotIn("BadNode", override)

    def test_hidden_child_option_is_skipped(self):
        override = get_pipeline_override_from_task_option(
            self.interface,
            {
                "低阶柜台": {
                    "value": "No",
                    "branches": {
                        "Yes": {
                            "金兔子": {"value": {"数量": "5"}, "hidden": True},
                        },
                        "No": {"金兔子": {"value": {"数量": "0"}}},
                    },
                }
            },
        )
        self.assertFalse(override["Parent"]["enabled"])
        self.assertEqual(["0"], override["GoldRabbit"]["expected"])

    def test_skips_internal_and_resource_fields(self):
        override = get_pipeline_override_from_task_option(
            self.interface,
            {
                "_speedrun_config": {"enabled": True},
                "resource": "官服",
                "resource_options": {"资源选项": "覆盖"},
                "作战关卡": "4-20 厄险",
            },
        )
        self.assertEqual("MainChapter_4", override["EnterTheShow"]["next"])
        self.assertNotIn("_speedrun_config", override)

    def test_resource_task_merges_global_then_resource_options(self):
        override = get_pipeline_override_from_task_option(
            self.interface,
            {
                "resource_options": {"资源选项": "覆盖"},
                "global_options": {"全局选项": "默认"},
            },
            task_id=_RESOURCE_,
            global_options={"全局选项": "默认"},
        )
        self.assertEqual("resource", override["Shared"]["level"])

    def test_select_with_dict_value_produces_no_override(self):
        with patch("app.core.utils.pipeline_helper.logger.error"):
            override = get_pipeline_override_from_task_option(
                self.interface,
                {"作战关卡": {"value": {"bad": "dict"}}},
            )
        self.assertNotIn("EnterTheShow", override)


class TestGetControllerOptionPipelineOverride(unittest.TestCase):
    def test_extracts_declared_controller_options_only(self):
        interface = _base_interface()
        override = get_controller_option_pipeline_override(
            interface,
            {
                "controller_type": "Win32",
                "controller_options": {
                    "控制器选项": "ctrl",
                    "未声明选项": "ignored",
                },
            },
        )
        self.assertTrue(override["CtrlNode"]["enabled"])
        self.assertNotIn("EnterTheShow", override)

    def test_returns_empty_when_controller_has_no_option_field(self):
        interface = {
            "controller": [{"name": "Adb", "type": "Adb"}],
            "option": _base_interface()["option"],
        }
        override = get_controller_option_pipeline_override(
            interface,
            {
                "controller_type": "Adb",
                "controller_options": {"控制器选项": "ctrl"},
            },
        )
        self.assertEqual({}, override)


if __name__ == "__main__":
    unittest.main()
