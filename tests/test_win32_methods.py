import unittest

from maa.define import MaaWin32InputMethodEnum, MaaWin32ScreencapMethodEnum

from app.core.utils.win32_methods import (
    resolve_method_value,
    resolve_win32_input_method,
    resolve_win32_screencap_method,
)
from app.utils.controller_utils import should_search_desktop_windows_on_ui_thread


class Win32MethodResolutionTests(unittest.TestCase):
    def test_missing_screencap_uses_interface_background_not_gdi(self):
        resolved = resolve_win32_screencap_method(None, fallback="Background")
        self.assertNotEqual(resolved, 1)
        members = getattr(MaaWin32ScreencapMethodEnum, "__members__", {})
        if "Background" in members:
            self.assertEqual(resolved, int(members["Background"].value))
        else:
            self.assertEqual(resolved, 2 | 16)

    def test_missing_screencap_uses_interface_screendc(self):
        resolved = resolve_win32_screencap_method(None, fallback="ScreenDC")
        members = getattr(MaaWin32ScreencapMethodEnum, "__members__", {})
        if "ScreenDC" in members:
            self.assertEqual(resolved, int(members["ScreenDC"].value))
        else:
            self.assertEqual(resolved, 32)

    def test_zero_and_minus_one_screencap_fall_back_to_interface(self):
        members = getattr(MaaWin32ScreencapMethodEnum, "__members__", {})
        expected = int(members["PrintWindow"].value) if "PrintWindow" in members else 16
        self.assertEqual(
            resolve_win32_screencap_method(0, fallback="PrintWindow"),
            expected,
        )
        self.assertEqual(
            resolve_win32_screencap_method(-1, fallback="PrintWindow"),
            expected,
        )

    def test_explicit_gdi_is_kept(self):
        self.assertEqual(resolve_win32_screencap_method(1, fallback="ScreenDC"), 1)

    def test_default_without_interface_is_dxgi_not_gdi(self):
        resolved = resolve_win32_screencap_method(None)
        self.assertEqual(
            resolved, int(MaaWin32ScreencapMethodEnum.DXGI_DesktopDup.value)
        )
        self.assertNotEqual(resolved, 1)

    def test_missing_input_uses_interface_name(self):
        resolved = resolve_win32_input_method(None, fallback="Seize")
        self.assertEqual(resolved, int(MaaWin32InputMethodEnum.Seize.value))

    def test_resolve_method_value_accepts_enum_name(self):
        aliases = {"background": 18, "screendc": 32}
        self.assertEqual(
            resolve_method_value("Background", aliases=aliases, default=4),
            18,
        )


class DeviceFinderThreadPolicyTests(unittest.TestCase):
    def test_win32_and_macos_search_on_ui_thread(self):
        self.assertTrue(should_search_desktop_windows_on_ui_thread("win32"))
        self.assertTrue(should_search_desktop_windows_on_ui_thread("Win32"))
        self.assertTrue(should_search_desktop_windows_on_ui_thread("macos"))
        self.assertFalse(should_search_desktop_windows_on_ui_thread("adb"))
        self.assertFalse(should_search_desktop_windows_on_ui_thread(None))


if __name__ == "__main__":
    unittest.main()
