from pathlib import Path
from typing import Any

from app.core.facade._snapshot import snapshot
from app.core.item import ConfigItem
from app.core.service.config_service import ConfigService, JsonConfigRepository


class ConfigFacade:
    """配置域的显式 View API。"""

    def __init__(
        self,
        service: ConfigService,
        repository: JsonConfigRepository,
    ) -> None:
        self._service = service
        self._repository = repository

    @property
    def current_config_id(self) -> str:
        return self._service.current_config_id

    @property
    def main_config_path(self) -> Path:
        return self._repository.main_config_path

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
