import jsonc
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


from app.utils.logger import logger
from app.common.constants import PRE_CONFIGURATION, POST_ACTION
from app.core.Item import ConfigItem, TaskItem, CoreSignalBus


class JsonConfigRepository:
    """JSON配置存储库实现"""

    def __init__(
        self,
        main_config_path: Path,
        configs_dir: Path,
        interface: Optional[Dict[str, Any]] = None,
    ):
        self.main_config_path = main_config_path
        self.configs_dir = configs_dir
        self.interface = interface or {}

        # 确保目录存在
        if not self.configs_dir.exists():
            self.configs_dir.mkdir(parents=True)

        if not self.main_config_path.exists():
            # 如果 interface 为空，说明加载失败
            if not self.interface:
                interface_path_jsonc = Path.cwd() / "interface.jsonc"
                interface_path_json = Path.cwd() / "interface.json"

                # 检查配置文件是否存在
                if (
                    not interface_path_jsonc.exists()
                    and not interface_path_json.exists()
                ):
                    raise FileNotFoundError(
                        f"无有效资源配置文件: {interface_path_jsonc} 或 {interface_path_json}"
                    )

            logger.debug("使用 interface 配置创建默认配置")

            bundle_name = self.interface.get("name", "Default Bundle")
            default_main_config = {
                "curr_config_id": "",
                "config_list": [],
                "bundle": {
                    bundle_name: {
                        "path": "./",
                    }
                },
            }
            self.save_main_config(default_main_config)

    def load_main_config(self) -> Dict[str, Any]:
        """加载主配置"""
        try:
            with open(self.main_config_path, "r", encoding="utf-8") as f:
                return jsonc.load(f)
        except Exception as e:
            raise

    def save_main_config(self, config_data: Dict[str, Any]) -> bool:
        """保存主配置"""
        try:
            with open(self.main_config_path, "w", encoding="utf-8") as f:
                jsonc.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            raise

    def load_config(self, config_id: str) -> Dict[str, Any]:
        """加载子配置"""
        config_file = self.configs_dir / f"{config_id}.json"
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件 {config_file} 不存在")
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return jsonc.load(f)
        except Exception as e:
            raise

    def save_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        """保存子配置"""
        try:
            config_file = self.configs_dir / f"{config_id}.json"
            with open(config_file, "w", encoding="utf-8") as f:
                jsonc.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            raise

    def delete_config(self, config_id: str) -> bool:
        """删除子配置"""
        config_file = self.configs_dir / f"{config_id}.json"
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件 {config_file} 不存在")
        try:
            config_file.unlink()
            return True
        except Exception as e:
            raise

    def list_configs(self) -> List[str]:
        """列出所有子配置ID"""
        try:
            return [f.stem for f in self.configs_dir.glob("*.json") if f.is_file()]
        except Exception as e:
            raise


class ConfigService:
    """配置服务实现"""

    def __init__(self, config_repo: JsonConfigRepository, signal_bus: CoreSignalBus):
        self.repo = config_repo
        self.signal_bus = signal_bus
        self._main_config: Optional[Dict[str, Any]] = None
        self._config_changed_callback: Optional[Callable[[str], None]] = None

        # 加载主配置
        self.load_main_config()
        if self._main_config and not self._main_config.get("curr_config_id"):

            # Get the first bundle from the bundle dictionary
            bundle_dict = self._main_config.get("bundle", {})
            # Use the first bundle in the dictionary
            first_bundle_name = next(iter(bundle_dict.keys()), "Default Bundle")
            bundle = bundle_dict.get(first_bundle_name, {"path": "./"})

            default_config_item = ConfigItem(
                name="Default Config",
                item_id=ConfigItem.generate_id(),
                tasks=[],
                know_task=[],
                bundle=bundle,
            )

            self._main_config["config_list"].append(default_config_item.item_id)
            self._main_config["curr_config_id"] = default_config_item.item_id
            self.current_config_id = self.create_config(default_config_item)

    def register_on_change(self, callback: Callable[[str], None]) -> None:
        """注册配置变更回调，供服务协调器触发内部同步。"""
        self._config_changed_callback = callback

    def load_main_config(self) -> bool:
        """加载主配置"""
        try:
            self._main_config = self.repo.load_main_config()
            return True
        except Exception as e:
            print(f"加载主配置失败: {e}")
            return False

    def save_main_config(self) -> bool:
        """保存主配置"""
        if self._main_config is None:
            print("没有主配置可保存")
            return False

        return self.repo.save_main_config(self._main_config)

    @property
    def current_config_id(self) -> str:
        """获取当前配置ID"""
        return self._main_config.get("curr_config_id", "") if self._main_config else ""

    @current_config_id.setter
    def current_config_id(self, value: str) -> bool:
        """设置当前配置ID"""
        if self._main_config is None:
            return False

        # 验证配置ID是否存在
        if value and value not in self._main_config.get("config_list", []):
            print(f"配置ID {value} 不存在")
            return False

        self._main_config["curr_config_id"] = value

        # 保存主配置并发出信号
        if self.save_main_config():
            if self._config_changed_callback:
                try:
                    self._config_changed_callback(value)
                except Exception as exc:
                    logger.error(f"配置变更回调执行失败: {exc}")
            self.signal_bus.config_changed.emit(value)
            return True

        return False

    def get_config(self, config_id: str) -> Optional[ConfigItem]:
        """获取指定配置"""
        config_data = self.repo.load_config(config_id)
        if not config_data:
            return None

        return ConfigItem.from_dict(config_data)

    def get_current_config(self) -> ConfigItem:
        """获取当前配置"""
        if not self.current_config_id:
            raise ValueError("当前配置ID为空")
        config = self.get_config(self.current_config_id)
        if not config:
            raise ValueError("当前配置不存在")
        return config

    def save_config(self, config_id: str, config_data: ConfigItem) -> bool:
        """保存指定配置"""
        if self._main_config is None:
            return False

        # 如果配置ID不在主配置列表中，添加到主配置
        if config_id not in self._main_config.get("config_list", []):
            self._main_config["config_list"].append(config_id)
            self.save_main_config()

        # config_data 应为 ConfigItem，直接转换为 dict 保存
        return self.repo.save_config(config_id, config_data.to_dict())

    def create_config(self, config: ConfigItem) -> str:
        """创建新配置，统一使用 uuid 生成 id"""
        if not config.item_id:
            config.item_id = ConfigItem.generate_id()

        # If no tasks provided, add base tasks only.
        # Task generation from interface should be handled by TaskService
        init_controller = self.repo.interface["controller"][0]["name"]
        init_resource = self.repo.interface["resource"][0]["name"]
        if not config.tasks:
            default_tasks = [
                TaskItem(
                    name="Pre-Configuration",
                    item_id=PRE_CONFIGURATION,
                    is_checked=True,
                    task_option={
                        "controller_type": init_controller,
                        "resource": init_resource,
                    },
                    is_special=False,  # 基础任务，不是特殊任务
                ),
                TaskItem(
                    name="Post-Action",
                    item_id=POST_ACTION,
                    is_checked=True,
                    task_option={},
                    is_special=False,  # 基础任务，不是特殊任务
                ),
            ]
            config.tasks = default_tasks

        if self.save_config(config.item_id, config):
            return config.item_id
        return ""

    def update_config(self, config_id: str, config_data: ConfigItem) -> bool:
        """更新配置"""
        return self.save_config(config_id, config_data)

    def delete_config(self, config_id: str) -> bool:
        """删除配置（禁止删除最后一个配置）"""
        if self._main_config is None:
            return False

        # 从主配置列表中移除
        if config_id in self._main_config.get("config_list", []):
            self._main_config["config_list"].remove(config_id)

            # 如果删除的是当前配置，需要更新当前配置
            if self.current_config_id == config_id:
                if self._main_config["config_list"]:
                    self.current_config_id = self._main_config["config_list"][0]
                else:
                    self.current_config_id = ""

            # 保存主配置
            self.save_main_config()

        # 删除子配置文件
        return self.repo.delete_config(config_id)

    def list_configs(self) -> List[Dict[str, Any]]:
        """列出所有配置的概要信息"""
        if self._main_config is None:
            return []
        configs = []
        for config_id in self._main_config.get("config_list", []):
            config_data = self.repo.load_config(config_id)
            if config_data:
                # 只返回概要信息，不包含任务详情
                summary = {"item_id": config_id, "name": config_data.get("name", "")}
                configs.append(summary)
        return configs

    def get_bundle(self, bundle_name: str) -> dict:
        """获取bundle数据（新格式：bundle为dict，key为名字）"""
        if self._main_config and "bundle" in self._main_config:
            bundle = self._main_config["bundle"]
            if isinstance(bundle, dict) and bundle_name in bundle:
                return bundle[bundle_name]
        raise FileNotFoundError(f"Bundle {bundle_name} not found")

    def list_bundles(self) -> List[str]:
        """列出所有bundle名称（新格式：bundle为dict，key为名字）"""
        if self._main_config and "bundle" in self._main_config:
            bundle = self._main_config["bundle"]
            if isinstance(bundle, dict):
                return list(bundle.keys())
        return []
