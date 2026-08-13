from typing import Any

from app.core.facade._snapshot import snapshot
from app.core.item import TaskItem
from app.core.service.option_service import OptionService


class OptionFacade:
    """选项域的显式 View API。"""

    def __init__(self, service: OptionService) -> None:
        self._service = service

    @property
    def current_task_id(self) -> str | None:
        return self._service.current_task_id

    @property
    def current_options(self) -> dict[str, Any]:
        return snapshot(self._service.current_options)

    def clear_selection(self) -> None:
        self._service.clear_selection()

    def get_options(self) -> dict[str, Any]:
        return snapshot(self._service.get_options())

    def get_option(self, option_key: str) -> Any:
        return snapshot(self._service.get_option(option_key))

    def get_form_structure(self) -> dict[str, Any] | None:
        return snapshot(self._service.get_form_structure())

    def get_setting_form_structure(self) -> dict[str, Any]:
        return snapshot(self._service.get_setting_form_structure())

    def get_form_field(self, field_name: str) -> dict[str, Any] | None:
        return snapshot(self._service.get_form_field(field_name))

    def is_option_visible(self, option_def: dict[str, Any]) -> bool:
        return self._service.is_option_visible(snapshot(option_def))

    def process_option_def(
        self,
        option_def: dict[str, Any],
        all_options: dict[str, Any],
        option_name: str = "",
    ) -> dict[str, Any]:
        return snapshot(
            self._service.process_option_def(
                snapshot(option_def),
                snapshot(all_options),
                option_name,
            )
        )

    def update_option(self, option_key: str, option_value: Any) -> bool:
        return self._service.update_option(option_key, snapshot(option_value))

    def update_options(self, options: dict[str, Any]) -> bool:
        return self._service.update_options(snapshot(options))

    def update_controller_options(self, options: dict[str, Any]) -> bool:
        return self._service.update_controller_options(snapshot(options))

    def normalize_post_action(
        self,
        action: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return snapshot(self._service.normalize_post_action(snapshot(action)))

    def update_post_action(self, action: dict[str, Any]) -> bool:
        return self._service.update_post_action(snapshot(action))

    def get_current_speedrun_config(self) -> dict[str, Any]:
        return snapshot(self._service.get_current_speedrun_config())

    def update_speedrun_config(self, config: dict[str, Any]) -> bool:
        return self._service.update_speedrun_config(snapshot(config))

    def update_setting_options(self, options: dict[str, Any]) -> bool:
        return self._service.update_setting_options(snapshot(options))

    def update_resource_selection(self, resource_name: str) -> bool:
        return self._service.update_resource_selection(resource_name)

    def update_resource_options(
        self,
        resource_options: dict[str, Any],
        active_option_names: list[str],
    ) -> bool:
        return self._service.update_resource_options(
            snapshot(resource_options),
            list(active_option_names),
        )

    def get_task(self, task_id: str) -> TaskItem | None:
        return snapshot(self._service.task_service.get_task(task_id))
