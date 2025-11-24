"""
Interface i18n 管理器
用于将 interface.json 中的所有 $ 开头的文本翻译为目标语言
"""
import jsonc
from pathlib import Path
from typing import Dict, Any, Optional
from copy import deepcopy

from app.common.config import cfg
from app.utils.logger import logger


class InterfaceI18n:
    """Interface 翻译管理器（单例模式）"""
    
    _instance = None
    _translated_interface: Dict[str, Any] = {}
    _original_interface: Dict[str, Any] = {}
    _translations: Dict[str, str] = {}
    _current_language: str = "zh_cn"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = False
    
    def initialize(self, interface_path: Optional[Path] = None, language: Optional[str] = None):
        """
        初始化 Interface i18n
        
        Args:
            interface_path: interface.json 文件路径，默认为项目根目录
            language: 语言代码（如 "zh_cn", "en_us", "zh_hk"），默认从配置读取
        """
        if self._initialized:
            return
        
        # 确定 interface.json 路径
        if interface_path is None:
            # 优先尝试读取 interface.jsonc
            interface_path = Path.cwd() / "interface.jsonc"
            if not interface_path.exists():
                # 如果 interface.jsonc 不存在，再尝试 interface.json
                interface_path = Path.cwd() / "interface.json"
        
        # 加载原始 interface.json
        try:
            with open(interface_path, "r", encoding="utf-8") as f:
                self._original_interface = jsonc.load(f)
            logger.debug(f"加载 interface.json: {interface_path}")
        except FileNotFoundError:
            logger.error(f"未找到 interface.json: {interface_path}")
            self._original_interface = {}
            return
        except jsonc.JSONDecodeError as e:
            logger.error(f"interface.json 格式错误: {e}")
            self._original_interface = {}
            return
        
        # 设置当前语言
        if language:
            # 直接使用传入的语言代码
            self._current_language = language
        else:
            # 从配置获取语言设置（从 QFluentWidgets 的 language 配置映射）
            # Language.CHINESE_SIMPLIFIED → "zh_cn"
            # Language.ENGLISH → "en_us"
            # Language.CHINESE_TRADITIONAL → "zh_hk"
            language_map = {
                "Chinese (China)": "zh_cn",
                "Chinese (Hong Kong)": "zh_hk",
                "English": "en_us",
            }
            qt_locale = cfg.get(cfg.language)
            locale_name = qt_locale.value.name() if hasattr(qt_locale, 'value') else "Chinese (China)"
            self._current_language = language_map.get(locale_name, "zh_cn")
        
        # 加载翻译文件
        self._load_translations()
        
        # 翻译 interface
        self._translate_interface()
        
        self._initialized = True
    
    def _load_translations(self):
        """加载翻译文件"""
        if not self._original_interface:
            return
        
        # 从 interface.json 获取语言文件映射
        languages = self._original_interface.get("languages", {})
        translation_file = languages.get(self._current_language)
        
        if not translation_file:
            logger.warning(f"未找到语言 {self._current_language} 的翻译文件配置")
            return
        
        # 加载翻译文件
        translation_path = Path.cwd() / translation_file
        try:
            with open(translation_path, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
            logger.debug(f"已加载翻译文件: {translation_path} ({len(self._translations)} 条翻译)")
        except FileNotFoundError:
            logger.warning(f"未找到翻译文件: {translation_path}")
            self._translations = {}
        except json.JSONDecodeError as e:
            logger.error(f"翻译文件格式错误: {e}")
            self._translations = {}
    
    def _translate_text(self, text: str) -> str:
        """
        翻译单个文本
        
        Args:
            text: 待翻译的文本
        
        Returns:
            翻译后的文本
        """
        if not text:
            return text
        
        # 如果文本以 $ 开头，进行翻译
        if text.startswith("$"):
            key = text[1:]  # 去掉 $ 前缀
            return self._translations.get(key, key)  # 找不到翻译时返回 key
        
        # 不以 $ 开头的文本直接返回
        return text
    
    def _translate_interface(self):
        """翻译整个 interface.json"""
        if not self._original_interface:
            logger.warning("原始 interface.json 为空，无法翻译")
            self._translated_interface = {}
            return
        
        # 深拷贝原始数据
        self._translated_interface = deepcopy(self._original_interface)
        
        # 翻译顶层字段
        self._translate_dict(self._translated_interface)
        
        logger.debug(f"interface.json 翻译完成，当前语言: {self._current_language}")
    
    def _translate_dict(self, data: Any) -> Any:
        """
        递归翻译字典中的所有值
        
        Args:
            data: 要翻译的数据（可以是 dict, list, str 等）
        
        Returns:
            翻译后的数据
        """
        if isinstance(data, dict):
            # 递归翻译字典中的每个值
            for key, value in data.items():
                # 特殊处理 label, description, title 等字段
                if key in ('label', 'description', 'title', 'welcome') and isinstance(value, str):
                    data[key] = self._translate_text(value)
                else:
                    data[key] = self._translate_dict(value)
        
        elif isinstance(data, list):
            # 递归翻译列表中的每个元素
            for i, item in enumerate(data):
                data[i] = self._translate_dict(item)
        
        elif isinstance(data, str):
            # 直接翻译字符串（如果以 $ 开头）
            return self._translate_text(data)
        
        return data
    
    def get_translated_interface(self) -> Dict[str, Any]:
        """
        获取翻译后的 interface.json
        
        Returns:
            翻译后的 interface 字典
        """
        if not self._initialized:
            self.initialize()
        
        return self._translated_interface
    
    def get_original_interface(self) -> Dict[str, Any]:
        """
        获取原始的 interface.json
        
        Returns:
            原始 interface 字典
        """
        return self._original_interface
    
    def set_language(self, language: str):
        """
        设置当前语言
        
        Args:
            language: 语言代码，如 "zh_cn", "en_us"
        """
        if language == self._current_language:
            return
        
        self._current_language = language
        
        # 重新加载翻译
        self._load_translations()
        self._translate_interface()
    
    def refresh(self):
        """刷新翻译（当语言切换时调用）"""
        if not self._original_interface:
            logger.warning("原始 interface.json 为空，无法刷新翻译")
            return
        
        # 重新翻译
        self._translate_interface()
        logger.info(f"interface.json 翻译已刷新，当前语言: {self._current_language}")


# 全局单例实例
_interface_i18n = InterfaceI18n()


def get_interface_i18n(language: Optional[str] = None) -> InterfaceI18n:
    """
    获取 Interface i18n 单例实例
    
    Args:
        language: 语言代码（如 "zh_cn", "en_us", "zh_hk"），默认从配置读取
    
    Returns:
        InterfaceI18n 实例
    
    Example:
        >>> interface_i18n = get_interface_i18n("en_us")
        >>> translated = interface_i18n.get_translated_interface()
        >>> print(translated["task"][0]["label"])  # 已翻译的任务标签
    """
    if not _interface_i18n._initialized:
        _interface_i18n.initialize(language=language)
    return _interface_i18n


def refresh_interface_translation():
    """
    刷新 interface 翻译
    
    在语言切换后调用此函数，重新翻译 interface.json
    
    Example:
        >>> from app.utils.i18n_manager import get_interface_i18n
        >>> interface_i18n = get_interface_i18n()
        >>> interface_i18n.set_language("en_us")
        >>> refresh_interface_translation()
    """
    _interface_i18n.refresh()
