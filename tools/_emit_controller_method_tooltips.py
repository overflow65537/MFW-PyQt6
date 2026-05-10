# Run: python tools/_emit_controller_method_tooltips.py
# Writes tools/_controller_method_tooltip_fragment.py (class-method bodies, 4-space indent).

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "_controller_method_tooltip_fragment.py"

WIN32_INPUT: dict[str, str] = {
    "Seize": """Description: Injects input on the target window thread; closest to real mouse/keyboard.
Speed: Fast.
Mouse capture: Yes (continuous capture of the window input queue).
Compatibility: High.
Admin rights: Usually not required; match elevation if the target runs elevated.""",
    "SendMessage": """Description: Synchronously posts window messages via SendMessage.
Speed: Medium.
Mouse capture: No.
Compatibility: Medium; some games/anti-cheat ignore synthetic messages.
Admin rights: Often depends on the target process (elevated targets need an elevated client).""",
    "PostMessage": """Description: Asynchronously posts window messages via PostMessage.
Speed: Medium.
Mouse capture: No.
Compatibility: Medium; some games/anti-cheat ignore synthetic messages.
Admin rights: Often depends on the target process (elevated targets need an elevated client).""",
    "LegacyEvent": """Description: Legacy event-injection path.
Speed: Medium.
Mouse capture: Yes.
Compatibility: Low.
Admin rights: Usually not required; depends on the target process.""",
    "PostThreadMessage": """Description: Posts messages to the window's owning thread.
Speed: Medium.
Mouse capture: No.
Compatibility: Low.
Admin rights: Often depends on the target process.""",
    "SendMessageWithCursorPos": """Description: Briefly moves the cursor to the target point, sends the message, then restores the cursor.
Speed: Medium.
Mouse capture: Brief cursor movement.
Compatibility: Medium.
Admin rights: Often depends on the target process.""",
    "PostMessageWithCursorPos": """Description: Briefly moves the cursor to the target point, sends the message, then restores the cursor.
Speed: Medium.
Mouse capture: Brief cursor movement.
Compatibility: Medium.
Admin rights: Often depends on the target process.""",
    "SendMessageWithWindowPos": """Description: Briefly moves the window so the target aligns with the current cursor, sends the message, then restores the window.
Speed: Medium.
Mouse capture: No (the window moves, not the cursor).
Compatibility: Medium; may fail for fullscreen or locked-layout games.
Admin rights: Often depends on the target process.""",
    "PostMessageWithWindowPos": """Description: Briefly moves the window so the target aligns with the current cursor, sends the message, then restores the window.
Speed: Medium.
Mouse capture: No (the window moves, not the cursor).
Compatibility: Medium; may fail for fullscreen or locked-layout games.
Admin rights: Often depends on the target process.""",
}

WIN32_SCREENCAP: dict[str, str] = {
    "GDI": """Description: GDI capture of the window client area.
Speed: Fast.
Mouse capture: No.
Compatibility: Medium.
Admin rights: Usually not required.
Background: Often fails while minimized.""",
    "FramePool": """Description: Windows.Graphics.Capture (Windows 10 1903+).
Speed: Very fast.
Mouse capture: No.
Compatibility: Medium.
Admin rights: Usually not required.
Background: Better for pseudo-minimized / quasi-background capture.""",
    "DXGI_DesktopDup": """Description: DXGI desktop duplication (full screen) then crop.
Speed: Very fast.
Mouse capture: No.
Compatibility: Lower (drivers / multi-GPU sensitive).
Admin rights: Usually not required.
Background: Full-screen duplication; not window-exclusive.""",
    "DXGI_DesktopDup_Window": """Description: Desktop duplication cropped to the window region.
Speed: Very fast.
Mouse capture: No.
Compatibility: Lower.
Admin rights: Usually not required.""",
    "PrintWindow": """Description: Capture via PrintWindow and related paths.
Speed: Medium.
Mouse capture: No.
Compatibility: Medium.
Admin rights: Usually not required.
Background: Friendlier to pseudo-minimized scenarios.""",
    "ScreenDC": """Description: Screen DC and other compatible paths.
Speed: Fast.
Mouse capture: No.
Compatibility: High.
Admin rights: Usually not required.
Background: Mostly foreground-oriented.""",
    "Foreground": """Description: Foreground preset (DXGI_DesktopDup_Window | ScreenDC).
Speed: Fast.
Mouse capture: No.
Compatibility: Medium to low.
Admin rights: Usually not required.""",
    "Background": """Description: Background preset (FramePool | PrintWindow).
Speed: Fast.
Mouse capture: No.
Compatibility: Medium.
Admin rights: Usually not required.""",
    "All": """Description: Bitwise OR of all Win32 capture flags.
Speed: Framework picks the fastest available method.
Mouse capture: No.
Compatibility: Varies by combination.
Admin rights: Usually not required.""",
}

ADB_SCREENCAP: dict[str, str] = {
    "EncodeToFileAndPull": """Description: Encodes to a file on the device, then adb pull.
Speed: Slow.
Mouse capture: N/A (device-side).
Compatibility: High.
Admin rights: Not required on PC; USB debugging authorization on the device.
Encoding: Lossless.""",
    "Encode": """Description: Encoded stream pulled over the adb pipe.
Speed: Slow.
Mouse capture: N/A (device-side).
Compatibility: High.
Admin rights: Not required.
Encoding: Lossless.""",
    "RawWithGzip": """Description: Raw frames with gzip compression.
Speed: Medium.
Mouse capture: N/A (device-side).
Compatibility: High.
Admin rights: Not required.
Encoding: Lossless.""",
    "RawByNetcat": """Description: Raw frames over netcat.
Speed: Fast.
Mouse capture: N/A (device-side).
Compatibility: Low (environment-dependent).
Admin rights: Not required.""",
    "MinicapDirect": """Description: Minicap direct connection.
Speed: Fast.
Mouse capture: N/A (device-side).
Compatibility: Low.
Admin rights: Not required.
Encoding: Lossy JPEG; may hurt template matching — not recommended.""",
    "MinicapStream": """Description: Minicap streaming.
Speed: Very fast.
Mouse capture: N/A (device-side).
Compatibility: Low.
Admin rights: Not required.
Encoding: Lossy JPEG — not recommended.""",
    "EmulatorExtras": """Description: Emulator-specific fast path (e.g. MuMu 12, LDPlayer 9).
Speed: Very fast.
Mouse capture: N/A (device-side).
Compatibility: Low (specific emulators).
Admin rights: Not required.
Encoding: Lossless.""",
    "All": """Description: All ADB capture flags enabled; framework benchmarks and picks one.
Speed: Fastest available on the device.
Mouse capture: N/A (device-side).
Compatibility: Device-dependent.
Admin rights: Not required.""",
    "Default": """Description: Framework default flag set (typically excludes netcat and lossy Minicap).
Speed: Best within the default set.
Mouse capture: N/A (device-side).
Compatibility: Medium to high.
Admin rights: Not required.""",
}

ADB_INPUT: dict[str, str] = {
    "AdbShell": """Description: Standard adb shell input commands.
Speed: Slow.
Mouse capture: N/A (injected on the device).
Compatibility: High.
Admin rights: Not required.""",
    "MinitouchAndAdbKey": """Description: Minitouch with adb key fallback.
Speed: Fast.
Mouse capture: N/A (device-side).
Compatibility: Medium.
Admin rights: Not required.""",
    "Maatouch": """Description: Maatouch protocol for touch injection.
Speed: Fast.
Mouse capture: N/A (device-side).
Compatibility: Medium.
Admin rights: Not required.""",
    "EmulatorExtras": """Description: Emulator extras (e.g. MuMu 12).
Speed: Fast.
Mouse capture: N/A (device-side).
Compatibility: Low (specific emulators).
Admin rights: Not required.""",
    "All": """Description: All ADB input flags; order EmulatorExtras > Maatouch > MinitouchAndAdbKey > AdbShell.
Speed: First available wins.
Mouse capture: N/A (device-side).
Compatibility: Device-dependent.
Admin rights: Not required.""",
    "Default": """Description: Default set with EmulatorExtras disabled; remaining methods by priority.
Speed: Device-dependent.
Mouse capture: N/A (device-side).
Compatibility: Medium to high.
Admin rights: Not required.""",
}


def _format_tr_call(text: str) -> str:
    """Emit self.tr( "line\\n" + ... ) for pyside lupdate."""
    lines = text.strip().split("\n")
    parts = [ln.replace("\\", "\\\\").replace('"', '\\"') for ln in lines]
    if not parts:
        return 'self.tr("")'
    chunks = [f'"{p}\\n"' for p in parts[:-1]]
    chunks.append(f'"{parts[-1]}"')
    joined = "\n                + ".join(chunks)
    return f"self.tr(\n                {joined}\n            )"


def _emit_dict_method(func_name: str, mapping: dict[str, str]) -> str:
    out_lines = [f"    def {func_name}(self, k: str) -> str:"]
    for key, text in mapping.items():
        out_lines.append(f'        if k == "{key}":')
        out_lines.append(f"            return {_format_tr_call(text)}")
    out_lines.append('        return self.tr("(No description for this method.)")')
    out_lines.append("")
    return "\n".join(out_lines)


def main() -> None:
    blocks: list[str] = [
        "    @staticmethod",
        "    def _method_key_for_combo_value(options: dict[str, Any], raw_value: Any) -> str:",
        '        """根据下拉项 userData 反查选项键名（与 options 中枚举名一致）。"""',
        "        try:",
        "            int_value = int(raw_value)",
        "        except (TypeError, ValueError):",
        '            return ""',
        "        for name, mapped in options.items():",
        "            try:",
        "                if int(mapped) == int_value:",
        "                    return str(name)",
        "            except (TypeError, ValueError):",
        "                continue",
        '        return ""',
        "",
        "    def _apply_controller_method_tooltips(",
        "        self, label: BodyLabel, combo: ComboBox, tip: str",
        "    ) -> None:",
        "        apply_fluent_tooltip(",
        "            label,",
        "            tip,",
        "            delay=300,",
        "            position=ToolTipPosition.BOTTOM,",
        "        )",
        "        apply_fluent_tooltip(",
        "            combo,",
        "            tip,",
        "            delay=300,",
        "            position=ToolTipPosition.BOTTOM,",
        "        )",
        "",
        '    def _controller_method_detail_text(self, category: str, method_key: str) -> str:',
        '        """Localized help for controller capture/input methods (UI source strings are English)."""',
        "        if not method_key or method_key == \"null\":",
        "            return self.tr(",
        '                "Description: No specific method (Null).\\n"',
        '                + "Speed: Depends on framework fallback.\\n"',
        '                + "Mouse capture: N/A (desktop).\\n"',
        '                + "Compatibility: Framework-defined.\\n"',
        '                + "Admin rights: Usually not required; elevate if the target process runs elevated."',
        "            )",
        "",
        '        if category == "win32_input":',
        "            return self._controller_method_detail_text_win32_input(method_key)",
        '        if category == "win32_screencap":',
        "            return self._controller_method_detail_text_win32_screencap(method_key)",
        '        if category == "adb_screencap":',
        "            return self._controller_method_detail_text_adb_screencap(method_key)",
        '        if category == "adb_input":',
        "            return self._controller_method_detail_text_adb_input(method_key)",
        '        return self.tr("(No description for this category.)")',
        "",
        _emit_dict_method("_controller_method_detail_text_win32_input", WIN32_INPUT),
        _emit_dict_method(
            "_controller_method_detail_text_win32_screencap", WIN32_SCREENCAP
        ),
        _emit_dict_method("_controller_method_detail_text_adb_screencap", ADB_SCREENCAP),
        _emit_dict_method("_controller_method_detail_text_adb_input", ADB_INPUT),
        "    def _sync_controller_method_detail_labels(self) -> None:",
        '        """在填充配置后刷新各「方式说明」在标签与下拉框上的 tooltip。"""',
        "        specs: list[tuple[str, str, dict[str, Any]]] = [",
        '            ("mouse_input_methods", "win32_input", self.WIN32_INPUT_METHOD_ALIAS_VALUES),',
        "            (",
        '                "keyboard_input_methods",',
        '                "win32_input",',
        "                self.WIN32_INPUT_METHOD_ALIAS_VALUES,",
        "            ),",
        "            (",
        '                "win32_screencap_methods",',
        '                "win32_screencap",',
        "                self.WIN32_SCREENCAP_METHOD_ALIAS_VALUES,",
        "            ),",
        '            ("screencap_methods", "adb_screencap", self.ADB_SCREENCAP_OPTIONS),',
        '            ("input_methods", "adb_input", self.ADB_INPUT_OPTIONS),',
        "        ]",
        "        for combo_key, category, options in specs:",
        "            combo = self.resource_setting_widgets.get(combo_key)",
        "            label = self.resource_setting_widgets.get(f\"{combo_key}_label\")",
        "            if not isinstance(combo, ComboBox) or not isinstance(label, BodyLabel):",
        "                continue",
        "            mk = self._method_key_for_combo_value(options, combo.itemData(combo.currentIndex()))",
        "            tip = self._controller_method_detail_text(category, mk)",
        "            self._apply_controller_method_tooltips(label, combo, tip)",
        "",
    ]

    OUT.write_text("\n".join(blocks), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
