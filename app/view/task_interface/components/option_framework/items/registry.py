"""Option item registry and factory."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.utils.logger import logger

if TYPE_CHECKING:
    from .base import OptionItemBase


class OptionItemRegistry:
    _registry: dict[str, type["OptionItemBase"]] = {}
    _default_type = "combobox"

    @classmethod
    def register(cls, type_name: str, item_class: type["OptionItemBase"]) -> None:
        cls._registry[type_name.lower()] = item_class
        logger.debug("注册选项类型: %s -> %s", type_name, item_class.__name__)

    @classmethod
    def create(
        cls,
        key: str,
        config: dict[str, Any],
        parent: Any | None = None,
    ) -> "OptionItemBase":
        type_name = config.get("type", cls._default_type)
        if isinstance(type_name, str):
            type_name = type_name.lower()

        item_class = cls._registry.get(type_name)
        if item_class is None:
            logger.warning(
                "未知的选项类型 '%s'，使用默认类型 '%s'",
                type_name,
                cls._default_type,
            )
            item_class = cls._registry.get(cls._default_type)
        if item_class is None:
            raise ValueError(f"默认选项类型 '{cls._default_type}' 未注册")
        return item_class(key, config, parent)


def register_default_types() -> None:
    from .checkbox import CheckBoxOptionItem
    from .combobox import ComboBoxOptionItem
    from .hotkey import HotkeyOptionItem
    from .input import InputOptionItem
    from .inputs import InputsOptionItem
    from .switch import SwitchOptionItem

    OptionItemRegistry.register("checkbox", CheckBoxOptionItem)
    OptionItemRegistry.register("combobox", ComboBoxOptionItem)
    OptionItemRegistry.register("select", ComboBoxOptionItem)
    OptionItemRegistry.register("switch", SwitchOptionItem)
    OptionItemRegistry.register("input", InputOptionItem)
    OptionItemRegistry.register("inputs", InputsOptionItem)
    OptionItemRegistry.register("hotkey", HotkeyOptionItem)


register_default_types()

__all__ = ["OptionItemRegistry", "register_default_types"]
