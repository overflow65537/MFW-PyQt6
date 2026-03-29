from pathlib import Path
from typing import Any, Dict, List

from app.core.item import ConfigItem
from app.core.service.config_service import ConfigService, JsonConfigRepository


class ConfigQueryService:
    """配置域只读/轻量查询入口。"""

    def __init__(
        self,
        config_service: ConfigService,
        config_repo: JsonConfigRepository,
    ) -> None:
        self._config_service = config_service
        self._config_repo = config_repo

    def get_bundle(self, bundle_name: str) -> Dict[str, Any]:
        return self._config_service.get_bundle(bundle_name)

    def get_bundle_choices(self) -> List[Dict[str, str]]:
        bundles: List[Dict[str, str]] = []
        for name in self._config_service.list_bundles():
            try:
                info = self._config_service.get_bundle(name)
            except FileNotFoundError:
                continue
            bundles.append(
                {
                    "id": str(name),
                    "name": str(info.get("name", name)),
                    "path": str(info.get("path", "")),
                }
            )
        return bundles

    def get_current_config(self) -> ConfigItem | None:
        return self._config_service.get_current_config()

    def get_config(self, config_id: str) -> ConfigItem | None:
        return self._config_service.get_config(config_id)

    def get_current_config_id(self) -> str:
        return self._config_service.current_config_id

    def get_bundle_path_for_config(self, config: ConfigItem | None) -> str:
        if config is None:
            return ""
        return self._config_service.get_bundle_path_for_config(config)

    def get_main_config_path(self) -> Path:
        return self._config_repo.main_config_path

    def get_available_config_choices(self) -> List[tuple[str, str]]:
        return [
            (info.get("item_id", ""), info.get("name", ""))
            for info in self._config_service.list_configs()
        ]

    def get_current_global_options(self) -> Dict[str, Any]:
        return self._config_service.get_current_global_options()

    def update_current_global_options(self, global_options: Dict[str, Any]) -> bool:
        return self._config_service.update_current_global_options(global_options)
