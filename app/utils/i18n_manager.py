"""国际化管理模块

提供 Qt 国际化和 interface.json 资源国际化的统一管理。
- Qt 使用 QLocale 和 QTranslator
- interface.json 使用 JSON 格式的翻译文件
- 两者通过语言映射表进行配合
"""

import json
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtCore import QLocale
from app.common.config import Language, cfg
from app.utils.logger import logger


class LanguageMapper:
    """语言映射器
    
    负责在 Qt 的 Language 枚举和 interface.json 的语言标识之间进行转换。
    """
    
    # Qt Language 到 interface.json 语言标识的映射
    QT_TO_INTERFACE = {
        Language.CHINESE_SIMPLIFIED: "zh_cn",
        Language.CHINESE_TRADITIONAL: "zh_hk",  # 或 "zh_tw"
        Language.ENGLISH: "en_us",
    }
    
    # interface.json 语言标识到 Qt Language 的映射（反向）
    INTERFACE_TO_QT = {
        "zh_cn": Language.CHINESE_SIMPLIFIED,
        "zh_hk": Language.CHINESE_TRADITIONAL,
        "zh_tw": Language.CHINESE_TRADITIONAL,
        "en_us": Language.ENGLISH,
    }
    
    @classmethod
    def qt_to_interface(cls, qt_language: Language) -> str:
        """将 Qt Language 转换为 interface.json 语言标识
        
        Args:
            qt_language: Qt 的 Language 枚举值
            
        Returns:
            interface.json 的语言标识，如 "zh_cn", "en_us"
        """
        return cls.QT_TO_INTERFACE.get(qt_language, "zh_cn")
    
    @classmethod
    def interface_to_qt(cls, interface_lang: str) -> Language:
        """将 interface.json 语言标识转换为 Qt Language
        
        Args:
            interface_lang: interface.json 的语言标识
            
        Returns:
            Qt 的 Language 枚举值
        """
        return cls.INTERFACE_TO_QT.get(interface_lang.lower(), Language.CHINESE_SIMPLIFIED)
    
    @classmethod
    def get_current_interface_language(cls) -> str:
        """获取当前程序使用的 interface.json 语言标识
        
        Returns:
            当前语言标识，如 "zh_cn", "en_us"
        """
        current_qt_language = cfg.get(cfg.language)
        return cls.qt_to_interface(current_qt_language)


class InterfaceI18n:
    """Interface.json 国际化管理器
    
    负责加载和管理 interface.json 的多语言翻译文件。
    """
    
    def __init__(self, interface_json_path: Path):
        """初始化国际化管理器
        
        Args:
            interface_json_path: interface.json 文件路径
        """
        self.interface_path = interface_json_path
        self.base_dir = interface_json_path.parent
        self.translations: Dict[str, Dict[str, str]] = {}
        self.current_language: str = "zh_cn"
        
        # 加载主 interface.json
        self.interface_data = self._load_json(interface_json_path)
        
        # 从 interface.json 获取语言文件映射
        self.language_files = self.interface_data.get("languages", {})
        
        # 加载所有语言翻译文件
        self._load_all_translations()
    
    def _load_json(self, path: Path) -> dict:
        """加载 JSON 文件
        
        Args:
            path: JSON 文件路径
            
        Returns:
            解析后的 JSON 数据
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载 JSON 文件失败: {path}, 错误: {e}")
            return {}
    
    def _load_all_translations(self):
        """加载所有语言的翻译文件"""
        for lang_key, filename in self.language_files.items():
            translation_path = self.base_dir / filename
            if translation_path.exists():
                translations = self._load_json(translation_path)
                self.translations[lang_key] = translations
                logger.info(f"加载语言文件: {lang_key} -> {filename}")
            else:
                logger.warning(f"语言文件不存在: {translation_path}")
                self.translations[lang_key] = {}
    
    def set_language(self, language: str):
        """设置当前语言
        
        Args:
            language: 语言标识，如 "zh_cn", "en_us"
        """
        if language in self.translations:
            self.current_language = language
            logger.info(f"切换 interface.json 语言: {language}")
        else:
            logger.warning(f"不支持的语言: {language}，使用默认语言 zh_cn")
            self.current_language = "zh_cn"
    
    def set_language_from_qt(self, qt_language: Language):
        """根据 Qt Language 设置当前语言
        
        Args:
            qt_language: Qt 的 Language 枚举值
        """
        interface_lang = LanguageMapper.qt_to_interface(qt_language)
        self.set_language(interface_lang)
    
    def translate(self, key: str) -> str:
        """翻译指定的键
        
        Args:
            key: 翻译键，可以带 $ 前缀，也可以不带
            
        Returns:
            翻译后的文本，如果没有找到则返回原始键
        """
        # 确保键带有 $ 前缀
        if not key.startswith("$"):
            key = f"${key}"
        
        # 获取当前语言的翻译
        current_translations = self.translations.get(self.current_language, {})
        
        # 查找翻译
        translated = current_translations.get(key)
        
        if translated:
            return translated
        
        # 如果没有找到，尝试使用默认语言（zh_cn）
        if self.current_language != "zh_cn":
            default_translations = self.translations.get("zh_cn", {})
            translated = default_translations.get(key)
            if translated:
                logger.debug(f"使用默认语言翻译: {key} -> {translated}")
                return translated
        
        # 如果还是没有找到，返回原始键（去掉 $ 前缀）
        logger.warning(f"未找到翻译: {key}")
        return key.lstrip("$")
    
    def translate_dict(self, data: dict) -> dict:
        """递归翻译字典中所有以 $ 开头的 label 和 description 字段
        
        Args:
            data: 需要翻译的字典
            
        Returns:
            翻译后的字典（深拷贝）
        """
        import copy
        result = copy.deepcopy(data)
        
        def _translate_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ["label", "description"] and isinstance(value, str) and value.startswith("$"):
                        obj[key] = self.translate(value)
                    elif isinstance(value, (dict, list)):
                        _translate_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    _translate_recursive(item)
        
        _translate_recursive(result)
        return result
    
    def get_translated_interface(self) -> dict:
        """获取翻译后的完整 interface.json 数据
        
        Returns:
            翻译后的 interface 数据
        """
        return self.translate_dict(self.interface_data)


# 全局单例
_interface_i18n: Optional[InterfaceI18n] = None


def init_interface_i18n(interface_json_path: Path):
    """初始化全局 interface.json 国际化管理器
    
    Args:
        interface_json_path: interface.json 文件路径
    """
    global _interface_i18n
    _interface_i18n = InterfaceI18n(interface_json_path)
    
    # 根据当前 Qt 语言设置初始语言
    current_qt_language = cfg.get(cfg.language)
    _interface_i18n.set_language_from_qt(current_qt_language)
    
    logger.info(f"Interface.json 国际化初始化完成，当前语言: {_interface_i18n.current_language}")


def get_interface_i18n() -> InterfaceI18n:
    """获取全局 interface.json 国际化管理器
    
    Returns:
        InterfaceI18n 实例
        
    Raises:
        RuntimeError: 如果未初始化
    """
    if _interface_i18n is None:
        raise RuntimeError("Interface.json 国际化管理器未初始化，请先调用 init_interface_i18n()")
    return _interface_i18n


def update_interface_language():
    """更新 interface.json 语言以匹配当前 Qt 语言
    
    当用户在设置中切换语言后调用此函数。
    """
    if _interface_i18n:
        current_qt_language = cfg.get(cfg.language)
        _interface_i18n.set_language_from_qt(current_qt_language)
        logger.info(f"Interface.json 语言已更新: {_interface_i18n.current_language}")
