"""PI hotkey 字符串与控制器虚拟键码之间的转换工具。"""

from __future__ import annotations

from typing import Any

from app.utils.logger import logger


HOTKEY_KEY_MAP: dict[str, dict[str, int]] = {
    "win32": {
        "BACKSPACE": 0x08,
        "TAB": 0x09,
        "ENTER": 0x0D,
        "SHIFT": 0x10,
        "CTRL": 0x11,
        "ALT": 0x12,
        "META": 0x5B,
        "PAUSE": 0x13,
        "CAPSLOCK": 0x14,
        "ESC": 0x1B,
        "SPACE": 0x20,
        "PAGEUP": 0x21,
        "PAGEDOWN": 0x22,
        "END": 0x23,
        "HOME": 0x24,
        "LEFT": 0x25,
        "UP": 0x26,
        "RIGHT": 0x27,
        "DOWN": 0x28,
        "INSERT": 0x2D,
        "DELETE": 0x2E,
        **{str(index): 0x30 + index for index in range(10)},
        **{chr(code): code for code in range(0x41, 0x5B)},
        **{f"F{index}": 0x6F + index for index in range(1, 13)},
    },
    "macos": {
        "BACKSPACE": 0x33,
        "TAB": 0x30,
        "ENTER": 0x24,
        "SHIFT": 0x38,
        "CTRL": 0x3B,
        "ALT": 0x3A,
        "META": 0x37,
        "CAPSLOCK": 0x39,
        "ESC": 0x35,
        "SPACE": 0x31,
        "PAGEUP": 0x74,
        "PAGEDOWN": 0x79,
        "END": 0x77,
        "HOME": 0x73,
        "LEFT": 0x7B,
        "UP": 0x7E,
        "RIGHT": 0x7C,
        "DOWN": 0x7D,
        "DELETE": 0x75,
        "0": 0x1D,
        "1": 0x12,
        "2": 0x13,
        "3": 0x14,
        "4": 0x15,
        "5": 0x17,
        "6": 0x16,
        "7": 0x1A,
        "8": 0x1C,
        "9": 0x19,
        "A": 0x00,
        "B": 0x0B,
        "C": 0x08,
        "D": 0x02,
        "E": 0x0E,
        "F": 0x03,
        "G": 0x05,
        "H": 0x04,
        "I": 0x22,
        "J": 0x26,
        "K": 0x28,
        "L": 0x25,
        "M": 0x2E,
        "N": 0x2D,
        "O": 0x1F,
        "P": 0x23,
        "Q": 0x0C,
        "R": 0x0F,
        "S": 0x01,
        "T": 0x11,
        "U": 0x20,
        "V": 0x09,
        "W": 0x0D,
        "X": 0x07,
        "Y": 0x10,
        "Z": 0x06,
        "F1": 0x7A,
        "F2": 0x78,
        "F3": 0x63,
        "F4": 0x76,
        "F5": 0x60,
        "F6": 0x61,
        "F7": 0x62,
        "F8": 0x64,
        "F9": 0x65,
        "F10": 0x6D,
        "F11": 0x67,
        "F12": 0x6F,
    },
    "adb": {
        "BACKSPACE": 67,
        "TAB": 61,
        "ENTER": 66,
        "SHIFT": 59,
        "CTRL": 113,
        "ALT": 57,
        "META": 117,
        "SPACE": 62,
        "ESC": 111,
        "DELETE": 112,
        "HOME": 3,
        "END": 123,
        "PAGEUP": 92,
        "PAGEDOWN": 93,
        "LEFT": 21,
        "RIGHT": 22,
        "UP": 19,
        "DOWN": 20,
        **{str(index): 7 + index for index in range(10)},
        **{chr(code): 29 + code - 0x41 for code in range(0x41, 0x5B)},
        **{f"F{index}": 130 + index for index in range(1, 13)},
    },
    "wlroots": {
        "BACKSPACE": 14,
        "TAB": 15,
        "ENTER": 28,
        "SHIFT": 42,
        "CTRL": 29,
        "ALT": 56,
        "META": 125,
        "SPACE": 57,
        "ESC": 1,
        "DELETE": 111,
        "HOME": 102,
        "END": 107,
        "PAGEUP": 104,
        "PAGEDOWN": 109,
        "LEFT": 105,
        "RIGHT": 106,
        "UP": 103,
        "DOWN": 108,
        "0": 11,
        "1": 2,
        "2": 3,
        "3": 4,
        "4": 5,
        "5": 6,
        "6": 7,
        "7": 8,
        "8": 9,
        "9": 10,
        "A": 30,
        "B": 48,
        "C": 46,
        "D": 32,
        "E": 18,
        "F": 33,
        "G": 34,
        "H": 35,
        "I": 23,
        "J": 36,
        "K": 37,
        "L": 38,
        "M": 50,
        "N": 49,
        "O": 24,
        "P": 25,
        "Q": 16,
        "R": 19,
        "S": 31,
        "T": 20,
        "U": 22,
        "V": 47,
        "W": 17,
        "X": 45,
        "Y": 21,
        "Z": 44,
        "F1": 59,
        "F2": 60,
        "F3": 61,
        "F4": 62,
        "F5": 63,
        "F6": 64,
        "F7": 65,
        "F8": 66,
        "F9": 67,
        "F10": 68,
        "F11": 87,
        "F12": 88,
    },
}

_KEY_ALIASES = {
    "CONTROL": "CTRL",
    "CMD": "META",
    "COMMAND": "META",
    "OPTION": "ALT",
    "RETURN": "ENTER",
    "ESCAPE": "ESC",
    "DEL": "DELETE",
    "INS": "INSERT",
    "PGUP": "PAGEUP",
    "PGDOWN": "PAGEDOWN",
    "PGDN": "PAGEDOWN",
}


def split_hotkey_combo(value: str) -> tuple[str, list[str]]:
    """按 PI 约定拆分组合键：末段为主键，其余为修饰键。"""
    parts = [part.strip() for part in str(value or "").split("+") if part.strip()]
    if not parts:
        return "", []
    return parts[-1], parts[:-1]


def hotkey_key_to_code(key_name: str, controller_type: str | None = None) -> int | None:
    """将按键名称映射为控制器支持的虚拟键码。"""
    normalized_type = str(controller_type or "").strip().lower()
    if normalized_type == "linux":
        normalized_type = "wlroots"

    key_map = HOTKEY_KEY_MAP.get(normalized_type)
    if key_map is None and normalized_type != "macos":
        key_map = HOTKEY_KEY_MAP["win32"]

    normalized_key = str(key_name or "").strip().upper().replace(" ", "")
    normalized_key = _KEY_ALIASES.get(normalized_key, normalized_key)
    key_code = key_map.get(normalized_key) if key_map else None
    if key_code is None:
        logger.warning(
            "未知热键按键，无法映射到虚拟键码"
            f" | key_name={key_name}"
            f" | controller_type={controller_type or '(fallback: Win32)'}"
        )
    return key_code


def resolve_controller_type(
    interface: dict[str, Any], controller_name: str | None
) -> str | None:
    """根据 PI controller.name 解析 controller.type。"""
    normalized_name = str(controller_name or "").strip().lower()
    if not normalized_name:
        return None
    for controller in interface.get("controller", []):
        if not isinstance(controller, dict):
            continue
        if str(controller.get("name", "")).strip().lower() == normalized_name:
            controller_type = str(controller.get("type", "")).strip()
            return controller_type or None
    return None


__all__ = [
    "HOTKEY_KEY_MAP",
    "hotkey_key_to_code",
    "resolve_controller_type",
    "split_hotkey_combo",
]
