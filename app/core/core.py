from pathlib import Path
from typing import List, Dict, Any
from copy import deepcopy
import time
import shutil

import jsonc

from PySide6.QtCore import QTimer, QObject, Qt, Slot

from app.core.item import (
    CoreSignalBus,
    ViewSignalBus,
    RunnerEvents,
    ConfigItem,
    TaskItem,
)
from app.core.service.config_service import ConfigService, JsonConfigRepository
from app.core.service.schedule_service import ScheduleService
from app.core.service.task_service import TaskService
from app.core.service.option_service import OptionService
from app.core.service.telemetry_service import TelemetryService
from app.core.service.interface_manager import get_interface_manager, InterfaceManager
from app.core.runner.runtime_context import RuntimeContext
from app.core.facade import (
    ConfigFacade,
    InterfaceFacade,
    OptionFacade,
    RuntimeFacade,
    ScheduleFacade,
    TaskFacade,
)
from app.utils.logger import logger
from app.common.signal_bus import signalBus


class _RunnerUiSignalBridge(QObject):
    """将 Runner 信号安全转发到全局 signalBus。"""

    @Slot(dict)
    def forward_callback(self, payload: dict):
        signalBus.callback.emit(payload)

    @Slot(str, str)
    def forward_log_output(self, level: str, text: str):
        signalBus.log_output.emit(level, text)

    @Slot(str)
    def forward_set_window_title(self, title: str):
        signalBus.set_window_title.emit(title)

    @Slot(str, str)
    def forward_task_status_changed(self, task_id: str, status: str):
        signalBus.task_status_changed.emit(task_id, status)

    @Slot(dict)
    def forward_task_flow_finished(self, payload: dict):
        signalBus.task_flow_finished.emit(payload)

    @Slot(dict)
    def forward_start_button_status(self, payload: dict):
        signalBus.start_button_status.emit(payload)

    @Slot()
    def forward_log_clear_requested(self):
        signalBus.log_clear_requested.emit()

    @Slot(str, str)
    def forward_info_bar_requested(self, level: str, message: str):
        signalBus.info_bar_requested.emit(level, message)

    @Slot(str)
    def forward_focus_toast(self, message: str):
        signalBus.focus_toast.emit(message)

    @Slot(str)
    def forward_focus_notification(self, message: str):
        signalBus.focus_notification.emit(message)

    @Slot(str)
    def forward_focus_dialog(self, message: str):
        signalBus.focus_dialog.emit(message)

    @Slot(str)
    def forward_focus_modal(self, message: str):
        signalBus.focus_modal.emit(message)

    @Slot(dict)
    def forward_controller_setup_hint_requested(self, payload: dict):
        signalBus.controller_setup_hint_requested.emit(payload)

    @Slot(dict)
    def forward_monitor_recognition_roi(self, payload: dict):
        signalBus.monitor_recognition_roi.emit(payload)


class _CoreUiSignalBridge(QObject):
    """将 Core 内部状态事件安全转发到 View 域信号。"""

    def __init__(self, view_signals: ViewSignalBus):
        super().__init__()
        self._view_signals = view_signals

    @Slot(str)
    def forward_config_changed(self, config_id: str):
        self._view_signals.config_changed.emit(config_id)

    @Slot()
    def forward_options_loaded(self):
        self._view_signals.options_loaded.emit()

    @Slot(object)
    def forward_option_updated(self, payload: object):
        self._view_signals.option_updated.emit(payload)

    @Slot(object)
    def forward_task_updated(self, task: object):
        self._view_signals.task_modified.emit(task)

    @Slot(list)
    def forward_schedules_changed(self, entries: list):
        self._view_signals.schedules_changed.emit(deepcopy(entries))


class ServiceCoordinator:
    """服务协调器，整合配置、任务和选项服务"""

    def __init__(
        self,
        main_config_path: Path,
        configs_dir: Path | None = None,
        interface_path: Path | str | None = None,
    ):
        # 初始化信号总线
        self._core_signals = CoreSignalBus()
        self._view_signals = ViewSignalBus()
        self._runtime_contexts: dict[str, RuntimeContext] = {}
        
        # 存储待显示的错误信息（用于在 UI 初始化完成后显示）
        self._pending_error_message: tuple[str, str] | None = None
        self._main_config_path = main_config_path

        # 根据传入参数或主配置中的 bundle.path 解析 interface 路径
        self._interface_path = self._resolve_interface_path(
            main_config_path, interface_path
        )

        # 确定配置目录
        if configs_dir is None:
            configs_dir = main_config_path.parent / "configs"

        # 先基于解析出的 interface 初始化管理器与数据，再交给仓库与服务使用
        self._interface_manager: InterfaceManager = get_interface_manager(
            interface_path=self._interface_path
        )
        self._interface: Dict = self._interface_manager.get_interface()

        # 初始化存储库和服务
        self._config_repo = JsonConfigRepository(
            main_config_path, configs_dir, interface=self._interface
        )
        
        # 尝试初始化 ConfigService 和 TaskService，如果配置加载失败则重置配置
        try:
            self._config_service = ConfigService(self._config_repo, self._core_signals)
            self._task_service = TaskService(
                self._config_service,
                self._core_signals,
                self._interface,
            )
        except (IndexError, ValueError, jsonc.JSONDecodeError, FileNotFoundError, Exception) as e:
            # 配置加载错误，尝试重置配置
            logger.error(f"配置加载失败: {e}")
            if self._handle_config_load_error(main_config_path, configs_dir, e):
                # 重置成功后重新初始化
                try:
                    self._config_service = ConfigService(
                        self._config_repo, self._core_signals
                    )
                    self._task_service = TaskService(
                        self._config_service,
                        self._core_signals,
                        self._interface,
                    )
                except Exception as retry_error:
                    logger.error(f"重置配置后重新初始化失败: {retry_error}")
                    raise
            else:
                # 重置失败，抛出原始错误
                raise
        
        self._option_service = OptionService(self._task_service, self._core_signals)
        self._active_runtime_context = self._get_or_create_runtime_context(
            self._config_service.current_config_id
        )
        self.telemetry_service = TelemetryService(
            self._active_runtime_context.events, self._interface
        )
        self._config_service.register_on_change(self._on_config_changed)
        self._schedule_service = ScheduleService()

        self._configs = ConfigFacade(
            self._config_service,
            self._config_repo,
            self._find_interface_file_in_dir,
        )
        self._tasks = TaskFacade(self._task_service)
        self._options = OptionFacade(self._option_service)
        self._schedules = ScheduleFacade(self._schedule_service)
        self._runtime = RuntimeFacade(lambda: self._active_runtime_context)
        self._interface_api = InterfaceFacade(
            self._interface_manager,
            lambda: self._interface_path,
            self._find_interface_file_in_dir,
        )

        self._runner_ui_bridge = _RunnerUiSignalBridge()
        self._core_ui_bridge = _CoreUiSignalBridge(self._view_signals)

        # 连接信号
        self._connect_signals()

        # 在主要内容初始化完毕后，清理无效的 bundle 索引（不删除配置）
        self._cleanup_invalid_bundles()

        self._finalize_bootstrap_interfaces()

        logger.info(f"资源版本: {self._interface.get('version', 'unknown')}")

    def _resolve_interface_path(
        self, main_config_path: Path, interface_path: Path | str | None
    ) -> Path | None:
        """根据传入路径或“当前激活配置”的 bundle.path 决定 interface 配置文件位置。

        优先级：
        1. 调用方显式传入的 interface_path
        2. multi_config.json 中 curr_config_id 对应配置文件里的 bundle.path
        3. multi_config.json 中第一个 bundle 的 path 下的 interface.jsonc/interface.json（兼容旧逻辑）
        4. 返回 None，交由 InterfaceManager 自行在 CWD 下探测
        """
        # 1. 显式传入时直接使用
        if interface_path:
            return Path(interface_path)

        # 2. 从主配置和“当前激活配置”解析 bundle.path
        try:
            if not main_config_path.exists():
                return None

            with open(main_config_path, "r", encoding="utf-8") as f:
                main_cfg: Dict[str, Any] = jsonc.load(f)

            # 2.1 优先使用当前激活配置（curr_config_id）对应配置里的 bundle
            curr_config_id = main_cfg.get("curr_config_id")
            if curr_config_id:
                configs_dir = main_config_path.parent / "configs"
                curr_config_path = configs_dir / f"{curr_config_id}.json"
                if curr_config_path.exists():
                    try:
                        with open(curr_config_path, "r", encoding="utf-8") as cf:
                            curr_cfg: Dict[str, Any] = jsonc.load(cf)
                        raw_bundle = curr_cfg.get("bundle")
                        bundle_name = self._normalize_bundle_name(raw_bundle)
                        candidate = self._resolve_interface_path_from_bundle(
                            bundle_name
                        )
                        if candidate:
                            logger.info(
                                f"从当前激活配置 {curr_config_id} 解析到 interface 路径: {candidate}"
                            )
                            return candidate
                    except Exception as e:
                        logger.warning(
                            f"从当前配置 {curr_config_id} 解析 interface 路径失败: {e}"
                        )

            # 2.2 兜底：使用 multi_config.json 里的第一个 bundle（兼容旧行为）
            bundle = main_cfg.get("bundle")
            if isinstance(bundle, dict) and bundle:
                first_bundle_name = next(iter(bundle.keys()))
                bundle_info = bundle.get(first_bundle_name, {})
                bundle_path_str = bundle_info.get("path")
                if bundle_path_str:
                    base_dir = Path(bundle_path_str)
                    if not base_dir.is_absolute():
                        base_dir = Path.cwd() / base_dir

                    candidate = self._find_interface_file_in_dir(base_dir)
                    if candidate:
                        logger.info(f"从主配置解析到 interface 路径: {candidate}")
                        return candidate

                    logger.warning(
                        f"在 bundle 路径 {base_dir} 下未找到 interface.jsonc/interface.json"
                    )

            discovered = self._discover_migrated_bundle_interface_path()
            if discovered:
                logger.info(
                    f"从 bundle 目录中发现迁移后的 interface 路径: {discovered}"
                )
                return discovered

            return None
        except Exception as e:
            logger.warning(f"从主配置解析 interface 路径失败: {e}")
            return None

    def _normalize_bundle_name(self, raw_bundle: Any) -> str | None:
        """从配置中的 bundle 字段推断 bundle 名称。

        兼容多种旧格式：
        - 新格式："MPA"
        - 旧格式1：{"MPA": {"name": "MPA", "path": "..."}}
        - 旧格式2：{"path": "..."} 或 {"name": "MPA", "path": "..."}
        """
        if isinstance(raw_bundle, str):
            return raw_bundle or None
        if isinstance(raw_bundle, dict):
            if not raw_bundle:
                return None
            first_key = next(iter(raw_bundle.keys()))
            first_val = raw_bundle[first_key]
            if isinstance(first_val, dict) and "path" in first_val:
                return first_key
            return str(raw_bundle.get("name") or first_key)
        return None

    @staticmethod
    def _find_interface_file_in_dir(base_dir: Path) -> Path | None:
        """在指定目录中查找 interface.jsonc 或 interface.json。"""
        for fname in ("interface.jsonc", "interface.json"):
            candidate = base_dir / fname
            if candidate.is_file():
                return candidate
        return None

    @staticmethod
    def _read_interface_name_from_file(interface_path: Path) -> str | None:
        """读取 interface 文件中的 name 字段。"""
        try:
            with open(interface_path, "r", encoding="utf-8") as handle:
                data = jsonc.load(handle)
            name = data.get("name") if isinstance(data, dict) else None
            return str(name).strip() if name else None
        except Exception:
            return None

    @classmethod
    def _pick_best_interface_candidate(
        cls,
        candidates: list[Path],
        bundle_name: str | None = None,
        assigned_bundle_dirs: set[Path] | None = None,
    ) -> Path:
        """在多个 bundle interface 候选中选择最匹配的一项。"""
        assigned_bundle_dirs = assigned_bundle_dirs or set()
        unassigned = [
            candidate
            for candidate in candidates
            if candidate.parent.resolve() not in assigned_bundle_dirs
        ]
        pool = unassigned or list(candidates)

        if bundle_name:
            for candidate in pool:
                if candidate.parent.name == bundle_name:
                    return candidate
            for candidate in pool:
                if cls._read_interface_name_from_file(candidate) == bundle_name:
                    return candidate

        migration_style = [
            candidate
            for candidate in pool
            if cls._read_interface_name_from_file(candidate) == candidate.parent.name
        ]
        if len(migration_style) == 1:
            return migration_style[0]
        if migration_style:
            pool = migration_style

        logger.warning(
            "bundle 目录下存在多个 interface 文件，默认使用: %s",
            pool[0],
        )
        return pool[0]

    def _collect_assigned_bundle_dirs(self) -> set[Path]:
        """收集主配置中已正确指向 interface 的 bundle 目录。"""
        assigned: set[Path] = set()
        try:
            if not hasattr(self, "_config_service") or not self._config_service:
                return assigned
            for bundle_key in self._config_service.list_bundles():
                bundle_info = self._config_service.get_bundle(bundle_key)
                bundle_path_str = str(bundle_info.get("path", "")).strip()
                if not bundle_path_str:
                    continue
                base_dir = Path(bundle_path_str)
                if not base_dir.is_absolute():
                    base_dir = (Path.cwd() / base_dir).resolve()
                found = self._find_interface_file_in_dir(base_dir)
                if found:
                    assigned.add(found.parent.resolve())
        except Exception as exc:
            logger.debug(f"收集已分配 bundle 目录失败: {exc}")
        return assigned

    def _collect_valid_bundle_interfaces_from_main_config(
        self, exclude_bundle: str | None = None
    ) -> list[Path]:
        """从 multi_config.json 收集已配置且可解析的 bundle interface 路径。"""
        candidates: list[Path] = []
        try:
            main_config_path = self._main_config_path
        except AttributeError:
            return candidates
        if not main_config_path or not main_config_path.exists():
            return candidates

        try:
            with open(main_config_path, "r", encoding="utf-8") as handle:
                main_cfg = jsonc.load(handle)
        except Exception:
            return candidates

        bundle_dict = main_cfg.get("bundle") or {}
        if not isinstance(bundle_dict, dict):
            return candidates

        for key, bundle_info in bundle_dict.items():
            if exclude_bundle and key == exclude_bundle:
                continue
            if not isinstance(bundle_info, dict):
                continue
            bundle_path_str = str(bundle_info.get("path", "")).strip()
            if not bundle_path_str or bundle_path_str.rstrip("/") in (".", "./"):
                continue
            base_dir = Path(bundle_path_str)
            if not base_dir.is_absolute():
                base_dir = Path.cwd() / base_dir
            found = self._find_interface_file_in_dir(base_dir)
            if found:
                candidates.append(found)
        return candidates

    def _discover_migrated_bundle_interface_path(
        self, bundle_name: str | None = None
    ) -> Path | None:
        """多资源迁移后，在 ./bundle/*/ 下搜索 interface 配置文件。"""
        sibling_candidates: list[Path] = []
        if bundle_name and hasattr(self, "_config_service") and self._config_service:
            try:
                for key in self._config_service.list_bundles():
                    if key == bundle_name:
                        continue
                    bundle_info = self._config_service.get_bundle(key)
                    bundle_path_str = str(bundle_info.get("path", "")).strip()
                    if not bundle_path_str or bundle_path_str.rstrip("/") in (".", "./"):
                        continue
                    base_dir = Path(bundle_path_str)
                    if not base_dir.is_absolute():
                        base_dir = Path.cwd() / base_dir
                    found = self._find_interface_file_in_dir(base_dir)
                    if found:
                        sibling_candidates.append(found)
            except Exception as exc:
                logger.debug(f"扫描 sibling bundle interface 失败: {exc}")
        elif bundle_name:
            sibling_candidates = self._collect_valid_bundle_interfaces_from_main_config(
                exclude_bundle=bundle_name
            )

        if len(sibling_candidates) == 1:
            return sibling_candidates[0]
        if len(sibling_candidates) > 1:
            return self._pick_best_interface_candidate(
                sibling_candidates,
                bundle_name,
                self._collect_assigned_bundle_dirs(),
            )

        bundle_root = Path.cwd() / "bundle"
        if not bundle_root.is_dir():
            return None

        if bundle_name:
            found = self._find_interface_file_in_dir(bundle_root / bundle_name)
            if found:
                return found

        candidates: list[Path] = []
        try:
            for sub in sorted(bundle_root.iterdir()):
                if sub.is_dir():
                    found = self._find_interface_file_in_dir(sub)
                    if found:
                        candidates.append(found)
        except OSError as exc:
            logger.warning(f"扫描 bundle 目录失败: {exc}")
            return None

        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]
        return self._pick_best_interface_candidate(
            candidates,
            bundle_name,
            self._collect_assigned_bundle_dirs(),
        )

    def _maybe_repair_bundle_path(
        self, bundle_name: str, interface_path: Path
    ) -> None:
        """发现迁移后的 interface 路径时，回写 bundle.path。"""
        if not bundle_name or not interface_path:
            return
        try:
            bundle_dir = interface_path.parent
            rel_path = bundle_dir.relative_to(Path.cwd())
            new_path = f"./{rel_path.as_posix()}"
        except ValueError:
            new_path = str(interface_path.parent)

        try:
            if hasattr(self, "_config_service") and self._config_service:
                current = self._config_service.get_bundle(bundle_name)
                current_path = str(current.get("path", "")).strip()
                if current_path != new_path:
                    self._configs.update_bundle_path(bundle_name, new_path)
        except Exception as exc:
            logger.warning(f"回写 bundle '{bundle_name}' 路径失败: {exc}")

    def _resolve_interface_path_from_bundle(
        self, bundle_name: str | None
    ) -> Path | None:
        """根据 bundle 名称解析 interface 路径。"""
        if not bundle_name:
            return None

        try:
            bundle_info = None
            if hasattr(self, "_config_service") and self._config_service:
                bundle_info = self._config_service.get_bundle(bundle_name)
            else:
                bundle_path_str = self._get_bundle_path_from_main_config(
                    bundle_name
                )
                if not bundle_path_str:
                    logger.warning(
                        f"未在主配置中找到 bundle: {bundle_name}"
                    )
                    return None
                bundle_info = {"path": bundle_path_str}
        except FileNotFoundError:
            logger.warning(f"未在主配置中找到 bundle: {bundle_name}")
            return None

        bundle_path_str = str(bundle_info.get("path", ""))
        if not bundle_path_str:
            return None

        base_dir = Path(bundle_path_str)
        if not base_dir.is_absolute():
            base_dir = Path.cwd() / base_dir

        candidate = self._find_interface_file_in_dir(base_dir)
        if candidate:
            return candidate

        logger.warning(
            f"在 bundle 路径 {base_dir} 下未找到 interface.jsonc/interface.json"
        )
        discovered = self._discover_migrated_bundle_interface_path(bundle_name)
        if discovered:
            logger.info(
                f"在 bundle 目录中发现迁移后的 interface: {discovered}"
            )
            self._maybe_repair_bundle_path(bundle_name, discovered)
            return discovered
        return None

    def _get_bundle_path_from_main_config(self, bundle_name: str) -> str | None:
        """在 config_service 可用前，从 multi_config.json 中查找 bundle 的 path。"""
        try:
            main_config_path = self._main_config_path
        except AttributeError as exc:
            logger.error("ServiceCoordinator 缺少 _main_config_path，无法从主配置解析 bundle 路径")
            raise
        if not main_config_path or not main_config_path.exists():
            return None

        try:
            with open(main_config_path, "r", encoding="utf-8") as mf:
                main_cfg: Dict[str, Any] = jsonc.load(mf)
        except Exception:
            return None

        bundle_dict = main_cfg.get("bundle") or {}
        if not isinstance(bundle_dict, dict):
            return None

        bundle_info = bundle_dict.get(bundle_name)
        if isinstance(bundle_info, dict):
            return bundle_info.get("path")

        return None

    def _handle_config_load_error(
        self, main_config_path: Path, configs_dir: Path, error: Exception
    ) -> bool:
        """处理配置加载错误：备份损坏的配置文件并用默认配置覆盖
        
        Args:
            main_config_path: 主配置文件路径
            configs_dir: 配置目录路径
            error: 发生的错误
            
        Returns:
            bool: 是否成功重置配置
        """
        try:
            logger.warning(f"检测到配置加载错误，开始重置配置: {error}")
            
            # 获取当前配置ID和bundle信息（如果存在）
            current_config_id = None
            bundle_name = None
            config_name = "Default Config"
            
            # 优先尝试从 config_service 获取当前配置ID（如果已初始化）
            try:
                if hasattr(self, "_config_service") and self._config_service:
                    current_config_id = self._config_service.current_config_id
            except Exception:
                pass
            
            # 如果无法从 config_service 获取，尝试从主配置文件中读取
            if not current_config_id:
                try:
                    if main_config_path.exists():
                        with open(main_config_path, "r", encoding="utf-8") as f:
                            main_config_data = jsonc.load(f)
                            current_config_id = main_config_data.get("curr_config_id")
                            
                            # 尝试获取bundle信息
                            if not bundle_name:
                                bundle_dict = main_config_data.get("bundle", {}) or {}
                                if bundle_dict:
                                    bundle_name = next(iter(bundle_dict.keys()), None)
                except Exception:
                    pass
            
            # 尝试从损坏的配置文件中读取名称和bundle（如果可能）
            if current_config_id:
                config_file = configs_dir / f"{current_config_id}.json"
                if config_file.exists():
                    try:
                        with open(config_file, "r", encoding="utf-8") as cf:
                            # 尝试读取，即使可能失败
                            try:
                                broken_config_data = jsonc.load(cf)
                                config_name = broken_config_data.get("name", "Default Config")
                                if not bundle_name:
                                    bundle_name = broken_config_data.get("bundle")
                            except:
                                # 如果读取失败，使用默认值
                                pass
                    except:
                        pass
            
            # 如果没有获取到bundle，使用interface中的默认值
            if not bundle_name:
                bundle_name = self._interface.get("name", "Default Bundle")
            
            # 备份损坏的配置文件
            timestamp = int(time.time())
            backup_success = False
            broken_config_file = None
            
            if current_config_id:
                config_file = configs_dir / f"{current_config_id}.json"
                if config_file.exists():
                    try:
                        backup_path = config_file.with_suffix(
                            f".broken.{timestamp}.json"
                        )
                        shutil.copy2(config_file, backup_path)
                        logger.info(f"已备份损坏的子配置文件到: {backup_path}")
                        broken_config_file = config_file
                        backup_success = True
                    except Exception as e:
                        logger.error(f"备份子配置文件失败: {e}")
            
            # 如果找不到损坏的配置文件，无法修复
            if not broken_config_file or not broken_config_file.exists():
                logger.error("无法找到损坏的配置文件，无法修复")
                error_message = f"Config load failed. Unable to locate corrupted config file for recovery. Error details: {str(error)}"
                self._pending_error_message = ("error", error_message)
                return False
            
            # 确保 current_config_id 不为 None（如果为 None，从文件名中提取）
            if not current_config_id:
                # 从 broken_config_file 的文件名中提取 config_id
                config_id_from_file = broken_config_file.stem
                if config_id_from_file.startswith("c_"):
                    current_config_id = config_id_from_file
                else:
                    # 如果无法从文件名提取，生成新的 ID
                    current_config_id = ConfigItem.generate_id()
                    logger.warning(f"无法获取配置ID，生成新的ID: {current_config_id}")
            else:
                # 确保 current_config_id 是字符串类型
                current_config_id = str(current_config_id)
            
            # 确保 bundle_name 不为 None
            if not bundle_name:
                bundle_name = self._interface.get("name", "Default Bundle")
            bundle_name = str(bundle_name)
            
            # 创建默认配置项（使用相同的config_id和bundle）
            init_controller = self._interface.get("controller", [{}])[0].get("name", "")
            init_resource = self._interface.get("resource", [{}])[0].get("name", "")
            
            from app.common.constants import _RESOURCE_, _CONTROLLER_, POST_ACTION
            
            default_tasks = [
                TaskItem(
                    name="Controller",
                    item_id=_CONTROLLER_,
                    is_checked=True,
                    task_option={
                        "controller_type": init_controller,
                    },
                ),
                TaskItem(
                    name="Resource",
                    item_id=_RESOURCE_,
                    is_checked=True,
                    task_option={
                        "resource": init_resource,
                        "setting_options": {},
                    },
                ),
                TaskItem(
                    name="Post-Action",
                    item_id=POST_ACTION,
                    is_checked=True,
                    task_option={},
                ),
            ]
            
            default_config_item = ConfigItem(
                name=config_name,
                item_id=current_config_id,
                tasks=default_tasks,
                know_task=[],
                bundle=bundle_name,
                interface_task_list_materialized=False,
            )
            
            # 将默认配置写入到损坏的配置文件中（覆盖）
            try:
                config_data = default_config_item.to_dict()
                with open(broken_config_file, "w", encoding="utf-8") as f:
                    jsonc.dump(config_data, f, indent=4, ensure_ascii=False)
                logger.info(f"已用默认配置覆盖损坏的配置文件: {broken_config_file}")
            except Exception as e:
                logger.error(f"覆盖损坏的配置文件失败: {e}")
                return False
            
            # 重新初始化配置仓库和服务
            self._config_repo = JsonConfigRepository(
                main_config_path, configs_dir, interface=self._interface
            )
            
            # 存储错误信息，等待 UI 初始化完成后显示
            # 使用英文作为基础消息，在 UI 层使用 tr 进行翻译
            if backup_success:
                error_message = f"Config load failed, automatically reset to default. Backup of corrupted config file completed. Error details: {str(error)}"
            else:
                error_message = f"Config load failed, automatically reset to default. Failed to backup corrupted config file. Error details: {str(error)}"
            self._pending_error_message = ("error", error_message)
            logger.info("Stored error message, waiting for UI initialization to complete")
            
            return True
            
        except Exception as e:
            logger.error(f"Exception occurred while handling config load error: {e}")
            error_message = f"Config load failed and error occurred while resetting config: {str(e)}"
            self._pending_error_message = ("error", error_message)
            return False

    def _cleanup_invalid_bundles(self) -> None:
        """检查 bundle.path 对应的 interface.json 是否存在，不存在则仅删除主配置中的 bundle 索引。

        注意：不会删除引用这些 bundle 的配置，交由后续逻辑按需处理。
        """
        try:
            bundle_names = self._config_service.list_bundles()
        except Exception as exc:
            logger.warning(f"读取 bundle 列表失败，跳过清理: {exc}")
            return

        if not bundle_names:
            return

        invalid_bundles: list[str] = []
        for name in bundle_names:
            iface_path = self._resolve_interface_path_from_bundle(name)
            if iface_path is None:
                logger.warning(
                    f"Bundle '{name}' 的 interface.json/interface.jsonc 未找到，将从主配置中移除索引"
                )
                invalid_bundles.append(name)

        if not invalid_bundles:
            return

        for name in invalid_bundles:
            logger.info(f"从主配置中移除无效 bundle 索引: {name}")
            if not self._config_service.delete_bundle(name):
                logger.warning(f"保存主配置时出错（清理无效 bundle '{name}' 后）")

    def _update_interface_path_for_config(self, config_id: str):
        """根据配置的 bundle 更新 interface 路径（如果需要）。

        Args:
            config_id: 配置ID
        """
        if not config_id:
            return

        config = self._config_service.get_config(config_id)
        if not config:
            return
        try:
            bundle_name = config.bundle
        except AttributeError as exc:
            logger.error(f"配置 {config_id} 缺少 bundle 字段，无法更新 interface 路径")
            raise
        if not bundle_name:
            return

        # 根据配置的 bundle 名称解析新的 interface 路径
        new_interface_path = self._resolve_interface_path_from_bundle(bundle_name)

        # 如果路径发生变化，需要重新加载 interface
        if new_interface_path and new_interface_path != self._interface_path:
            logger.info(
                f"检测到配置 {config_id} 的 bundle 路径变化，"
                f"从 {self._interface_path} 切换到 {new_interface_path}"
            )
            self._reload_interface(new_interface_path)

    def refresh_interface_for_current_config(self) -> None:
        """按当前配置和最新 bundle 路径刷新 interface。"""
        config_id = self._config_service.current_config_id
        if config_id:
            self._update_interface_path_for_config(config_id)
            return
        new_path = self._resolve_interface_path(self._main_config_path, None)
        if new_path and new_path != self._interface_path:
            self._reload_interface(new_path)

    def _reload_interface(self, interface_path: Path | str | None):
        """重新加载 interface 并更新相关服务。

        Args:
            interface_path: 新的 interface 文件路径
        """
        # 更新保存的路径
        self._interface_path = interface_path

        # 重新加载 interface
        self._interface_manager.reload(interface_path=self._interface_path)
        self._interface = self._interface_manager.get_interface()

        # 更新相关服务的 interface 数据
        self._config_repo.interface = self._interface
        self._task_service.reload_interface(self._interface)
        self.telemetry_service.configure_from_interface(self._interface)

    def _get_or_create_runtime_context(self, config_id: str) -> RuntimeContext:
        """Return the runtime context owned by one persistent configuration."""
        normalized_id = str(config_id or "")
        if not normalized_id:
            raise ValueError("Cannot create RuntimeContext without config_id")
        context = self._runtime_contexts.get(normalized_id)
        if context is None:
            context = RuntimeContext(
                normalized_id,
                task_service=self._task_service,
                config_service=self._config_service,
                run_config_callback=self._run_configuration_from_post_action,
            )
            self._runtime_contexts[normalized_id] = context
        return context

    async def _run_configuration_from_post_action(self, config_id: str) -> None:
        """在目标配置的 RuntimeContext 中继续完成后任务链。"""
        if not await self.run_configuration(config_id, clear_logs=True):
            logger.warning("完成后指定的配置无法运行: %s", config_id)

    def get_running_config_ids(self) -> list[str]:
        """Return configuration ids whose RuntimeContext still owns a live runtime."""
        return [
            config_id
            for config_id, context in self._runtime_contexts.items()
            if context.is_running
        ]

    async def stop_running_configuration(
        self,
        *,
        config_id: str | None = None,
        manual: bool = True,
    ) -> bool:
        """Stop the single live runtime without switching the active UI context."""
        running_ids = self.get_running_config_ids()
        if not running_ids:
            return False

        # The optional id is validated by the command layer. The current runtime
        # model still permits only one live task, so stop that task without
        # switching the UI context.
        target_id = running_ids[0]
        context = self._runtime_contexts[target_id]
        await context.task_runner.stop_task(manual=manual)
        return True

    async def run_configuration(
        self,
        config_id: str,
        *,
        clear_logs: bool = False,
    ) -> bool:
        """Atomically select and run one configuration's RuntimeContext."""
        target_id = str(config_id or "").strip()
        if not target_id or self._config_service.get_config(target_id) is None:
            return False

        running_ids = self.get_running_config_ids()
        if any(running_id != target_id for running_id in running_ids):
            logger.warning(
                "Cannot run %s while another configuration is active: %s",
                target_id,
                ", ".join(running_ids),
            )
            return False
        if target_id in running_ids:
            return False

        if self._config_service.current_config_id != target_id:
            if not self.select_config(target_id):
                return False
        if self._config_service.current_config_id != target_id:
            return False

        context = self._activate_runtime_context(target_id)
        if clear_logs:
            context.logs.clear()

        # Capture the target runner before awaiting so later UI switches cannot
        # redirect this run to another RuntimeContext.
        await RuntimeFacade(lambda: context).run()
        return True

    def get_runtime_context(self, config_id: str | None = None) -> RuntimeContext:
        """Return a configuration runtime, defaulting to the active one."""
        target_id = config_id or self._config_service.current_config_id
        return self._get_or_create_runtime_context(target_id)

    @staticmethod
    def _runtime_signal_bindings(context: RuntimeContext, bridge: _RunnerUiSignalBridge):
        events = context.events
        return (
            (events.callback, bridge.forward_callback),
            (events.log_output, bridge.forward_log_output),
            (events.set_window_title, bridge.forward_set_window_title),
            (events.task_status_changed, bridge.forward_task_status_changed),
            (events.task_flow_finished, bridge.forward_task_flow_finished),
            (events.start_button_status, bridge.forward_start_button_status),
            (events.log_clear_requested, bridge.forward_log_clear_requested),
            (events.info_bar_requested, bridge.forward_info_bar_requested),
            (events.focus_toast, bridge.forward_focus_toast),
            (events.focus_notification, bridge.forward_focus_notification),
            (events.focus_dialog, bridge.forward_focus_dialog),
            (events.focus_modal, bridge.forward_focus_modal),
            (
                events.controller_setup_hint_requested,
                bridge.forward_controller_setup_hint_requested,
            ),
            (events.monitor_recognition_roi, bridge.forward_monitor_recognition_roi),
        )

    def _connect_runtime_context(self, context: RuntimeContext) -> None:
        """Bridge only the active configuration's runner events to the UI."""
        for signal, slot in self._runtime_signal_bindings(
            context, self._runner_ui_bridge
        ):
            signal.connect(slot, Qt.ConnectionType.QueuedConnection)

    def _disconnect_runtime_context(self, context: RuntimeContext) -> None:
        for signal, slot in self._runtime_signal_bindings(
            context, self._runner_ui_bridge
        ):
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass

    def _activate_runtime_context(self, config_id: str) -> RuntimeContext:
        context = self._get_or_create_runtime_context(config_id)
        previous = getattr(self, "_active_runtime_context", None)
        if previous is context:
            return context
        if previous is not None and hasattr(self, "_runner_ui_bridge"):
            self._disconnect_runtime_context(previous)
        self._active_runtime_context = context
        if hasattr(self, "telemetry_service"):
            self.telemetry_service.set_runner_events(context.events)
        if hasattr(self, "_runner_ui_bridge"):
            self._connect_runtime_context(context)
        return context

    def _connect_signals(self):
        """Connect stable domain signals and the active runtime UI bridge."""
        signalBus.coordinator_reinit_requested.connect(self.reinit)
        self._core_signals.config_changed.connect(
            self._core_ui_bridge.forward_config_changed,
            Qt.ConnectionType.QueuedConnection,
        )
        self._core_signals.options_loaded.connect(
            self._core_ui_bridge.forward_options_loaded,
            Qt.ConnectionType.QueuedConnection,
        )
        self._core_signals.option_updated.connect(
            self._core_ui_bridge.forward_option_updated,
            Qt.ConnectionType.QueuedConnection,
        )
        self._core_signals.task_updated.connect(
            self._core_ui_bridge.forward_task_updated,
            Qt.ConnectionType.QueuedConnection,
        )
        self._schedule_service.schedules_changed.connect(
            self._core_ui_bridge.forward_schedules_changed,
            Qt.ConnectionType.QueuedConnection,
        )
        self._schedule_service.notification_requested.connect(
            self._runner_ui_bridge.forward_info_bar_requested,
            Qt.ConnectionType.QueuedConnection,
        )
        self._connect_runtime_context(self._active_runtime_context)

    def _on_config_changed(self, config_id: str):
        """Activate the config runtime, then refresh shared single-instance services."""
        if not config_id:
            return

        self._activate_runtime_context(config_id)
        self._update_interface_path_for_config(config_id)
        self._task_service.on_config_changed(config_id)
        self._option_service.clear_selection()

    # region configuration compatibility methods
    def update_bundle_path(
        self, bundle_name: str, new_path: str, bundle_display_name: str | None = None
    ) -> bool:
        """兼容入口；新调用应使用 configs.update_bundle_path。"""
        return self._configs.update_bundle_path(
            bundle_name,
            new_path,
            bundle_display_name,
        )

    def delete_bundle(self, bundle_name: str) -> bool:
        """兼容入口；新调用应使用 configs.delete_bundle。"""
        return self._configs.delete_bundle(bundle_name)

    def get_presets(self) -> List[Dict[str, Any]]:
        """获取 interface 中定义的所有预设配置列表。

        Returns:
            预设列表，每个元素是一个预设字典（含 name, label, description, icon, task 等字段）。
            如果没有预设则返回空列表。
        """
        presets = self._interface.get("preset", [])
        if not isinstance(presets, list):
            return []
        return presets

    def add_config(
        self,
        config_item: ConfigItem,
        preset_name: str | None = None,
        shared_tasks: list | None = None,
    ) -> str:
        """添加配置，传入 ConfigItem 对象，返回新配置ID

        Args:
            config_item: 配置项对象
            preset_name: 可选的预设名称。若指定且能找到预设，则仅物化 preset.task 中的任务（含 enabled/option）；否则按全 interface 物化。
            shared_tasks: 可选的分享任务列表。若指定则优先于 preset 用于初始化任务。
        """
        new_id = self._config_service.create_config(config_item)
        if new_id:
            # Select the new config
            self._config_service.current_config_id = new_id

            if shared_tasks is not None:
                self._task_service.init_config_from_shared(shared_tasks)
            elif preset_name:
                preset = self._find_preset(preset_name)
                if preset:
                    self._task_service.init_config_from_preset(preset)
                else:
                    self._task_service.init_new_config()
            else:
                self._task_service.init_new_config()

            # Notify UI incrementally
            self._view_signals.config_added.emit(
                self._config_service.get_config(new_id)
            )
        return new_id

    def _find_preset(self, preset_name: str) -> Dict[str, Any] | None:
        """根据预设名称查找预设配置。

        Args:
            preset_name: 预设的 name 字段值

        Returns:
            匹配的预设字典，未找到返回 None
        """
        presets = self.get_presets()
        for preset in presets:
            if isinstance(preset, dict) and preset.get("name") == preset_name:
                return preset
        return None

    def _collect_config_display_names(self) -> set[str]:
        names: set[str] = set()
        try:
            for entry in self._config_service.list_configs():
                n = entry.get("name")
                if isinstance(n, str) and n.strip():
                    names.add(n.strip())
        except Exception:
            pass
        return names

    @staticmethod
    def _unique_config_display_name(base: str, used: set[str]) -> str:
        b = base.strip() or "Config"
        if b not in used:
            return b
        i = 2
        while f"{b} ({i})" in used:
            i += 1
        return f"{b} ({i})"

    def _finalize_bootstrap_interfaces(self) -> None:
        """首次无主配置：有可用 preset 时物化 N 条子配置；否则走「单默认 + 可选追加 preset」逻辑。"""
        pairs = self._config_service.consume_bootstrap_preset_pairs()
        if pairs:
            for cid, preset_key in pairs:
                if not self.select_config(cid):
                    logger.warning("bootstrap: select_config failed for %s", cid)
                    continue
                preset = self._find_preset(preset_key)
                if preset:
                    self._task_service.init_config_from_preset(preset)
                else:
                    self._task_service.init_new_config()
                try:
                    self._view_signals.config_added.emit(
                        self._config_service.get_config(cid)
                    )
                except Exception:
                    pass
            self.select_config(pairs[0][0])
            return
        self._maybe_bootstrap_configs_from_presets()

    def _maybe_bootstrap_configs_from_presets(self) -> None:
        """首次无主配置仅创建 Default Config 后：若 interface 含 preset，为除 default 外的每项再建子配置并应用预设。"""
        if not self._config_service.consume_bootstrap_without_curr_config():
            return
        presets = self.get_presets()
        if not presets:
            return
        original_id = self._config_service.current_config_id
        if not original_id:
            return
        try:
            seed = self._config_service.get_config(original_id)
        except Exception:
            logger.exception("从预设物化子配置：无法读取种子配置")
            return
        if not seed:
            return
        bundle_name = seed.bundle or ""
        used_names = self._collect_config_display_names()
        for preset in presets:
            if not isinstance(preset, dict):
                continue
            raw_name = preset.get("name")
            if not isinstance(raw_name, str) or not raw_name.strip():
                continue
            preset_key = raw_name.strip()
            if preset_key.lower() == "default":
                continue
            if not self._find_preset(preset_key):
                continue
            base_label = str(
                preset.get("label") or preset.get("name") or preset_key
            ).strip()
            if not base_label:
                base_label = preset_key
            display_name = self._unique_config_display_name(base_label, used_names)
            used_names.add(display_name)
            new_item = ConfigItem(
                name=display_name,
                item_id=ConfigItem.generate_id(),
                tasks=[],
                know_task=[],
                bundle=bundle_name,
                interface_task_list_materialized=False,
            )
            try:
                self.add_config(new_item, preset_name=preset_key)
            except Exception:
                logger.exception(
                    "从预设物化子配置失败: preset name=%s", preset_key
                )
        try:
            self.select_config(original_id)
        except Exception:
            logger.exception("从预设物化子配置后恢复当前配置失败")

    def delete_config(self, config_id: str) -> bool:
        """删除配置，传入 config id"""
        context = self._runtime_contexts.get(config_id)
        if context is not None and context.is_running:
            logger.warning(
                "Configuration %s is still running; deletion refused",
                config_id,
            )
            return False
        ok = self._config_service.delete_config(config_id)
        if ok:
            removed = self._runtime_contexts.pop(config_id, None)
            if removed is not None and removed is not self._active_runtime_context:
                removed.deleteLater()
            # notify UI incremental removal
            self._view_signals.config_removed.emit(config_id)
        return ok

    def select_config(self, config_id: str) -> bool:
        """选择配置，传入 config id"""
        # 验证配置存在
        if not self._config_service.get_config(config_id):
            return False

        # 使用 ConfigService setter，回调将同步任务和选项
        self._config_service.current_config_id = config_id
        return self._config_service.current_config_id == config_id

    # endregion

    # region 任务相关方法

    def modify_task(self, task: TaskItem, idx: int = -2) -> bool:
        """修改或添加任务：传入 TaskItem，如果列表中没有对应 id 的任务，根据idx参数插入到指定位置，否则更新对应任务
        
        Args:
            task: 任务对象
            idx: 插入位置索引，默认为-2（倒数第二个位置）
        """
        ok = self._task_service.update_task(task, idx)
        if ok:
            self._view_signals.task_modified.emit(task)
        return ok

    def update_task_checked(self, task_id: str, is_checked: bool) -> bool:
        """更新任务选中状态"""
        return self.tasks.update_task_checked(task_id, is_checked)

    def modify_tasks(self, tasks: List[TaskItem]) -> bool:
        """批量修改/新增任务，成功后逐项发出 View 域更新事件。"""
        if not tasks:
            return True

        ok = self._task_service.update_tasks(tasks)
        if ok:
            # 兼容：对于希望逐项更新的监听者，仍发出逐项 task_updated 信号
            try:
                for t in tasks:
                    self._view_signals.task_modified.emit(t)
            except Exception:
                pass
        return ok

    def delete_task(self, task_id: str) -> bool:
        """删除任务，传入 task id，基础任务不可删除（通过特殊 id 区分）"""
        config = self._config_service.get_current_config()
        if not config:
            return False
        # 基础任务 id 以 r_ f_ 开头（资源和完成后操作）
        base_prefix = ("r_", "f_")
        for t in config.tasks:
            if t.item_id == task_id and t.item_id.startswith(base_prefix):
                return False
        ok = self._task_service.delete_task(task_id)
        if ok:
            self._view_signals.task_removed.emit(task_id)
        return ok

    def select_task(self, task_id: str) -> bool:
        """选中任务，传入 task id，并自动检查已知任务"""
        selected = self._option_service.select_task(task_id)
        self._task_service._check_know_task()
        return selected

    def reorder_tasks(self, new_order: List[str]) -> bool:
        """任务顺序更改，new_order 为 task_id 列表（新顺序）"""
        return self._task_service.reorder_tasks(new_order)

    # endregion
    def reinit(self):
        """重新初始化服务协调器，用于热更新完成后刷新资源"""
        logger.info("开始重新初始化服务协调器...")
        try:
            # 重新加载主配置
            self._config_repo.load_main_config()

            # 刷新 interface 数据
            self._interface_manager.reload(self._interface_path)
            self._interface = self._interface_manager.get_interface()
            self._config_repo.interface = self._interface

            # 重新初始化任务服务（刷新 interface 数据）
            self._task_service.reload_interface(self._interface)
            self.telemetry_service.configure_from_interface(self._interface)

            # 通知 UI 配置已更新
            current_config_id = self._config_service.current_config_id
            if current_config_id:
                self._core_signals.config_changed.emit(current_config_id)

            logger.info("服务协调器重新初始化完成")
        except Exception as e:
            logger.error(f"重新初始化服务协调器失败: {e}")

    async def run_tasks_flow(
        self, task_id: str | None = None
    ):
        """兼容入口；新调用应使用 runtime.run。"""
        return await self._runtime.run(task_id)

    async def stop_task_flow(self):
        """兼容入口；新调用应使用 runtime.stop。"""
        return await self._runtime.stop(manual=True)

    async def stop_task(self, *, manual: bool = False):
        """兼容入口；新调用应使用 runtime.stop。"""
        return await self._runtime.stop(manual=manual)

    def set_telemetry_enabled(self, enabled: bool) -> None:
        """更新用户遥测授权并立即应用。"""
        self.telemetry_service.set_user_enabled(bool(enabled))

    def is_telemetry_forced_disabled(self) -> bool:
        """开发/调试构建中强制禁用遥测。"""
        return self.telemetry_service.is_forced_disabled(self._interface)

    def shutdown_telemetry(self) -> None:
        """退出应用前刷新并关闭遥测。"""
        self.telemetry_service.shutdown()

    @property
    def interface(self) -> Dict[str, Any]:
        """兼容旧调用；新 View 代码应使用 interface_api.data。"""
        return self.interface_api.data

    @property
    def interface_path(self) -> Path | str | None:
        """返回当前生效的 interface 文件路径。"""
        return self._interface_path

    @property
    def configs(self) -> ConfigFacade:
        return self._configs

    @property
    def tasks(self) -> TaskFacade:
        return self._tasks

    @property
    def options(self) -> OptionFacade:
        return self._options

    @property
    def schedules(self) -> ScheduleFacade:
        return self._schedules

    @property
    def runtime(self) -> RuntimeFacade:
        return self._runtime

    @property
    def runner_events(self) -> RunnerEvents:
        """Compatibility alias for the active configuration events."""
        return self._active_runtime_context.events


    @property
    def interface_api(self) -> InterfaceFacade:
        return self._interface_api

    @property
    def view_signals(self) -> ViewSignalBus:
        """供 View 只读订阅的域事件入口。"""
        return self._view_signals
    
    def get_pending_error_message(self) -> tuple[str, str] | None:
        """获取并清除待显示的错误信息
        
        Returns:
            tuple[str, str] | None: (level, message) 或 None
        """
        if self._pending_error_message:
            msg = self._pending_error_message
            self._pending_error_message = None
            return msg
        return None
