import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.view.main_window.v5_style import build_v5_stylesheet


class V5StyleTests(unittest.TestCase):
    def test_build_v5_stylesheet_keeps_layout_rules(self):
        stylesheet = build_v5_stylesheet()

        self.assertIn("QFrame#V5HeroCard", stylesheet)
        self.assertIn("QLabel#V5ActionTitle", stylesheet)
        self.assertIn("QWidget#V5DashboardContent", stylesheet)

    def test_build_v5_stylesheet_does_not_define_global_light_dark_shell(self):
        stylesheet = build_v5_stylesheet()

        self.assertNotIn("QWidget#V5MainWindow", stylesheet)
        self.assertNotIn("QWidget#v5Navigation", stylesheet)
        self.assertNotIn("#1a1d23", stylesheet)
        self.assertNotIn("#14181d", stylesheet)


if __name__ == "__main__":
    unittest.main()