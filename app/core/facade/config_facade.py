from pathlib import Path
from typing import Any, Callable

from app.core.facade._snapshot import snapshot
from app.core.item import ConfigItem
from app.core.service.config_service import ConfigService, JsonConfigRepository


class ConfigFacade:
    """配置域的显式 View API。"""

    def __init__(
        self,
        service: ConfigService,
        repository: JsonConfigRepository,
        interface_file_finder: Callable[[Path], Path | None] | None = None,
    ) -> None:
        self._service = service
        self._repository = repository
        self._interface_file_finder = interface_file_finder

    @property
    def current_config_id(self) -> str:
        return self._service.current_config_id

    @property
    def main_config_path(self) -> Path:
        return self._repository.main_config_path

    def load_main_config(self) -> bool:
        """从磁盘重新加载主配置。"""
        return self._service.load_main_config()

    def list_configs(self) -> list[dict[str, Any]]:
        return snapshot(self._service.list_configs())

    def get_config(self, config_id: str) -> ConfigItem | None:
        return snapshot(self._service.get_config(config_id))

    def get_current_config(self) -> ConfigItem:
        return snapshot(self._service.get_current_config())

    def save_config(self, config_id: str, config: ConfigItem) -> bool:
        return self._service.save_config(config_id, snapshot(config))

    def rename_config(self, config_id: str, new_name: str) -> bool:
        return self._service.rename_config(config_id, new_name)

    def list_bundles(self) -> list[str]:
        return list(self._service.list_bundles())

    def get_bundle(self, bundle_name: str) -> dict[str, Any]:
        return snapshot(self._service.get_bundle(bundle_name))

    def get_current_bundle(self) -> dict[str, Any]:
        return snapshot(self._service.get_current_bundle())

    def update_bundle_path(
        self,
        bundle_name: str,
        new_path: str,
        bundle_display_name: str | None = None,
    ) -> bool:
        return self._service.update_bundle(
            bundle_name,
            new_path,
            bundle_display_name,
        )

    def delete_bundle(self, bundle_name: str) -> bool:
        return self._service.delete_bundle(bundle_name)

    def is_bundle_path_configured(
        self,
        bundle_name: str,
        expected_path: str | None = None,
    ) -> bool:
        try:
            bundle_path = str(self._service.get_bundle(bundle_name).get("path", ""))
        except FileNotFoundError:
            return False
        expected = expected_path or f"./bundle/{bundle_name}"
        normalized_path = bundle_path.replace("\\", "/").rstrip("/")
        normalized_expected = expected.replace("\\", "/").rstrip("/")
        return normalized_path == normalized_expected or normalized_path.endswith(
            normalized_expected.removeprefix(".")
        )

    def repair_bundle_paths(
        self,
        bundle_name: str,
        bundle_dir: Path,
    ) -> dict[str, bool]:
        """将缺失或失效的 bundle 索引修复为迁移后的目录。"""
        try:
            relative = bundle_dir.resolve().relative_to(Path.cwd().resolve())
            new_path = f"./{relative.as_posix()}"
        except ValueError:
            new_path = str(bundle_dir.resolve())

        targets: dict[str, str | None] = {bundle_name: bundle_name}
        for name in self._service.list_bundles():
            try:
                current_path = str(
                    self._service.get_bundle(name).get("path", "")
                ).strip()
            except FileNotFoundError:
                current_path = ""
            normalized = current_path.replace("\\", "/").rstrip("/")
            invalid = normalized in ("", ".", "./")
            if not invalid and self._interface_file_finder is not None:
                base_dir = Path(current_path)
                if not base_dir.is_absolute():
                    base_dir = Path.cwd() / base_dir
                invalid = self._interface_file_finder(base_dir) is None
            if invalid:
                targets[name] = bundle_name if name == bundle_name else None

        return {
            name: self._service.update_bundle(name, new_path, display_name)
            for name, display_name in targets.items()
        }

    def get_bundle_info_for_config(
        self, config: ConfigItem
    ) -> dict[str, str] | None:
        return snapshot(
            self._service.get_bundle_info_for_config(snapshot(config))
        )

    def get_bundle_path_for_config(self, config: ConfigItem) -> str:
        return self._service.get_bundle_path_for_config(snapshot(config))

    def get_current_setting_options(self) -> dict[str, Any]:
        return snapshot(self._service.get_current_setting_options())

    def get_current_global_options(self) -> dict[str, Any]:
        return snapshot(self._service.get_current_global_options())

    def update_current_setting_options(self, options: dict[str, Any]) -> bool:
        return self._service.update_current_setting_options(snapshot(options))

    def update_current_global_options(self, options: dict[str, Any]) -> bool:
        return self._service.update_current_global_options(snapshot(options))
