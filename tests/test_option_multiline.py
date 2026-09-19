from __future__ import annotations

import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from qfluentwidgets import TextEdit

_MODULE_PATH = (
    Path(__file__).parents[1]
    / "app/view/task_interface/components/option_framework/items/line_edit_factory.py"
)
_SPEC = spec_from_file_location("option_line_edit_factory_under_test", _MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_FACTORY = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FACTORY)

connect_option_input_changed = _FACTORY.connect_option_input_changed
create_option_line_edit = _FACTORY.create_option_line_edit
read_option_input = _FACTORY.read_option_input
write_option_input = _FACTORY.write_option_input


class TestOptionMultiline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_multiline_factory_roundtrip_and_change_signal(self):
        widget = create_option_line_edit({"multiline": True, "height": 120})
        self.assertIsInstance(widget, TextEdit)
        self.assertEqual(120, widget.height())

        changes: list[str] = []
        connect_option_input_changed(widget, changes.append)
        write_option_input(widget, "first\nsecond")

        self.assertEqual("first\nsecond", read_option_input(widget))
        self.assertEqual("first\nsecond", changes[-1])


if __name__ == "__main__":
    unittest.main()
