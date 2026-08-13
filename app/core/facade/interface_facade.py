from pathlib import Path
from typing import Any, Callable

from app.core.facade._snapshot import snapshot
from app.core.service.interface_manager import InterfaceManager


class InterfaceFacade:
    """Interface 配置的只读 View API。"""

    def __init__(
        self,
        manager: InterfaceManager,
        path_provider: Callable[[], Path | str | None],
        interface_file_finder: Callable[[Path], Path | None],
    ) -> None:
        self._manager = manager
        self._path_provider = path_provider
        self._interface_file_finder = interface_file_finder

    @property
    def data(self) -> dict[str, Any]:
        return snapshot(self._manager.get_interface())

    @property
    def original_data(self) -> dict[str, Any]:
        return snapshot(self._manager.get_original_interface())

    @property
    def path(self) -> Path | str | None:
        return self._path_provider()

    def get_current_language(self) -> str:
        return self._manager.get_language()

    def resolve_display_title(
        self, default_name: str = "ChainFlow Assistant"
    ) -> str:
        return self._manager.resolve_display_title(default_name)

    def resolve_display_name(
        self, default_name: str = "ChainFlow Assistant"
    ) -> str:
        return self._manager.resolve_display_name(default_name)

    def preview_interface(
        self,
        interface_path: Path | str,
        language: str | None = None,
    ) -> dict[str, Any]:
        return snapshot(
            self._manager.preview_interface(interface_path, language=language)
        )

    def find_interface_file(self, base_dir: Path) -> Path | None:
        return self._interface_file_finder(base_dir)
