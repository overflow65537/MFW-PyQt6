from copy import deepcopy
from typing import Any, Dict, List

from app.core.item import TaskItem
from app.core.service.option_service import OptionService
from app.core.service.task_service import TaskService


class TaskQueryService:
    """任务域只读/投影查询入口。"""

    def __init__(
        self,
        task_service: TaskService,
        option_service: OptionService,
    ) -> None:
        self._task_service = task_service
        self._option_service = option_service

    def get_task(self, task_id: str) -> TaskItem | None:
        return self._task_service.get_task(task_id)

    def get_tasks(self) -> List[TaskItem]:
        return self._task_service.get_tasks()

    def get_default_task_map(self) -> Dict[str, Any]:
        return dict(getattr(self._task_service, "default_option", {}))

    def get_task_option_value(
        self, task_id: str, option_key: str, default: Any = None
    ) -> Any:
        return self._task_service.get_task_option_value(task_id, option_key, default)

    def get_current_resource_name(self) -> str:
        return self._task_service.get_current_resource_name()

    def get_current_controller_type(self) -> str:
        return self._task_service.get_current_controller_type()

    def get_controller_ui_context(self, current_options: Dict[str, Any]) -> Dict[str, Any]:
        return self._task_service.get_controller_ui_context(current_options)

    def sync_controller_meta_fields(
        self,
        current_config: Dict[str, Any],
        controller_name: str,
        controller_info: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        return self._task_service.sync_controller_meta_fields(
            current_config, controller_name, controller_info
        )

    def ensure_controller_config(
        self,
        current_config: Dict[str, Any],
        controller_name: str,
        controller_info: Dict[str, Any],
        win32_default_mapping: Dict[str, Dict[str, Any]],
        gamepad_default_mapping: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        return self._task_service.ensure_controller_config(
            current_config,
            controller_name,
            controller_info,
            win32_default_mapping,
            gamepad_default_mapping,
        )

    def normalize_config_for_json(self, config: Any) -> Any:
        return self._task_service.normalize_config_for_json(config)

    def build_controller_task_option(
        self,
        current_config: Dict[str, Any],
        controller_type_mapping: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        return self._task_service.build_controller_task_option(
            current_config, controller_type_mapping
        )

    def build_resource_mapping(
        self, controller_type_mapping: Dict[str, Dict[str, Any]] | None = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        return self._task_service.build_resource_mapping(controller_type_mapping)

    def get_resources_for_controller(
        self,
        controller_label: str,
        controller_type_mapping: Dict[str, Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        return self._task_service.get_resources_for_controller(
            controller_label, controller_type_mapping
        )

    def get_current_resource_entry(
        self,
        controller_label: str,
        resource_name: str,
        controller_type_mapping: Dict[str, Dict[str, Any]] | None = None,
    ) -> Dict[str, Any] | None:
        return self._task_service.get_current_resource_entry(
            controller_label, resource_name, controller_type_mapping
        )

    def ensure_resource_matches_controller_resources(
        self, resources: List[Dict[str, Any]]
    ) -> str | None:
        return self._task_service.ensure_resource_matches_controller_resources(resources)

    def update_resource_options_hidden_state(
        self, current_resource_option_names: List[str]
    ) -> bool:
        return self._task_service.update_resource_options_hidden_state(
            current_resource_option_names
        )

    def get_resource_option_config(self, form_structure: Dict[str, Any]) -> Dict[str, Any]:
        return self._task_service.get_resource_option_config(form_structure)

    def get_current_option_task_id(self) -> str | None:
        return getattr(self._option_service, "current_task_id", None)

    def get_current_options(self) -> Dict[str, Any]:
        return self._option_service.get_options()

    def get_option_form_structure(self) -> Dict[str, Any] | None:
        return self._option_service.get_form_structure()

    def get_task_speedrun_payload(
        self, task_id: str
    ) -> tuple[TaskItem | None, Dict[str, Any] | None, Dict[str, Any]]:
        task, speedrun_config, state = self._task_service.get_task_speedrun_payload(task_id)
        if (
            task
            and speedrun_config is not None
            and self._option_service.current_task_id == task_id
        ):
            self._option_service.current_options["_speedrun_config"] = deepcopy(speedrun_config)
        return task, speedrun_config, state

    def process_option_def(
        self,
        option_def: Dict[str, Any],
        all_options: Dict[str, Dict[str, Any]],
        option_key: str = "",
    ) -> Dict[str, Any]:
        return self._option_service.process_option_def(option_def, all_options, option_key)

    def is_option_visible_for_controller(
        self, option_def: Dict[str, Any], current_controller: str
    ) -> bool:
        return self._option_service._is_option_visible_for_controller(
            option_def, current_controller
        )