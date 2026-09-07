import unittest

from app.core.utils.pretask_visibility import (
    has_visible_pretask_entries,
    is_pretask_entry_allowed,
    iter_visible_pretask_entries,
)


class PretaskVisibilityTests(unittest.TestCase):
    def test_no_pretask_configured(self):
        self.assertFalse(has_visible_pretask_entries({}, "adb", "res-a"))
        self.assertFalse(has_visible_pretask_entries({"pretask": []}, "adb", "res-a"))

    def test_pretask_object_form(self):
        interface = {
            "pretask": {
                "label": "Init",
                "exec": "init.exe",
            }
        }
        self.assertTrue(has_visible_pretask_entries(interface, "adb", "res-a"))

    def test_pretask_filtered_by_controller(self):
        interface = {
            "pretask": [
                {
                    "label": "Win only",
                    "exec": "init.exe",
                    "controller": ["win32"],
                }
            ]
        }
        self.assertTrue(has_visible_pretask_entries(interface, "win32", "res-a"))
        self.assertFalse(has_visible_pretask_entries(interface, "adb", "res-a"))

    def test_pretask_filtered_by_resource(self):
        interface = {
            "pretask": [
                {
                    "label": "Res B",
                    "exec": "init.exe",
                    "resource": ["res-b"],
                }
            ]
        }
        self.assertTrue(has_visible_pretask_entries(interface, "adb", "res-b"))
        self.assertFalse(has_visible_pretask_entries(interface, "adb", "res-a"))

    def test_empty_controller_or_resource_allows_all(self):
        entry = {"label": "Any", "exec": "init.exe", "controller": ["adb"]}
        self.assertTrue(is_pretask_entry_allowed(entry, "", "res-a"))
        self.assertTrue(is_pretask_entry_allowed(entry, "adb", ""))

    def test_iter_visible_pretask_entries_keeps_order(self):
        interface = {
            "pretask": [
                {"label": "First", "exec": "a.exe", "controller": ["adb"]},
                {"label": "Second", "exec": "b.exe"},
            ]
        }
        visible = iter_visible_pretask_entries(interface, "adb", "res-a")
        self.assertEqual([entry["label"] for entry in visible], ["First", "Second"])


if __name__ == "__main__":
    unittest.main()
