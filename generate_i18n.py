#!/usr/bin/env python3
"""
自动为 interface.json 生成 i18n 翻译文件
步骤:
1. 分析 interface.json 结构
2. 为需要翻译的文本添加 $ 前缀
3. 生成英文和繁体中文翻译文件
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Set

def read_interface(interface_path: Path) -> Dict[str, Any]:
    """读取 interface.json 文件"""
    with open(interface_path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_interface(interface_path: Path, data: Dict[str, Any]):
    """写入 interface.json 文件"""
    with open(interface_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def write_translation_file(file_path: Path, translations: Dict[str, str]):
    """写入翻译文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(translations, f, indent=2, ensure_ascii=False)

def collect_translatable_fields(data: Any, path: str = "") -> Set[str]:
    """
    收集所有需要翻译的字段
    这些字段通常是用户可见的文本内容
    """
    translatable_fields = set()
    
    if isinstance(data, dict):
        for key, value in data.items():
            # 需要翻译的字段类型
            if key in ("name", "entry", "doc", "field", "expected"):
                if isinstance(value, str) and value:
                    translatable_fields.add(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and item:
                            translatable_fields.add(item)
            # 递归处理嵌套结构
            new_path = f"{path}.{key}" if path else key
            translatable_fields.update(collect_translatable_fields(value, new_path))
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{path}[{i}]" if path else f"[{i}]"
            translatable_fields.update(collect_translatable_fields(item, new_path))
    
    return translatable_fields

def add_dollar_prefix(data: Any) -> Any:
    """
    为需要翻译的文本添加 $ 前缀
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ("name", "entry", "doc", "field", "expected"):
                if isinstance(value, str):
                    if value and not value.startswith("$"):
                        data[key] = f"${value}"
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, str) and item and not item.startswith("$"):
                            value[i] = f"${item}"
            # 递归处理嵌套结构
            else:
                data[key] = add_dollar_prefix(value)
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = add_dollar_prefix(item)
    
    return data

def generate_translation_files(interface: Dict[str, Any], output_dir: Path = Path.cwd()):
    """
    生成翻译文件
    """
    # 收集所有需要翻译的文本
    all_texts = collect_translatable_fields(interface)
    
    # 生成英文翻译文件
    en_translations = {text: text for text in all_texts}  # 初始值为原文
    en_file = output_dir / "interface_en_US.json"
    write_translation_file(en_file, en_translations)
    
    # 生成繁体中文翻译文件
    zh_hk_translations = {text: text for text in all_texts}  # 初始值为原文
    zh_hk_file = output_dir / "interface_zh_HK.json"
    write_translation_file(zh_hk_file, zh_hk_translations)
    
    # 在 interface.json 中添加语言配置
    if "languages" not in interface:
        interface["languages"] = {}
    
    interface["languages"] = {
        "zh_cn": "interface_zh_CN.json",  # 简体中文
        "en_us": "interface_en_US.json",    # 英文
        "zh_hk": "interface_zh_HK.json"     # 繁体中文
    }
    
    # 生成简体中文翻译文件
    zh_cn_translations = {text: text[1:] if text.startswith("$") else text for text in all_texts}  # 去掉 $ 前缀
    zh_cn_file = output_dir / "interface_zh_CN.json"
    write_translation_file(zh_cn_file, zh_cn_translations)

def main():
    """主函数"""
    interface_path = Path.cwd() / "interface.json"
    
    if not interface_path.exists():
        print(f"错误: 未找到 interface.json 文件在 {interface_path}")
        return
    
    # 读取原始 interface.json
    interface = read_interface(interface_path)
    
    # 为需要翻译的文本添加 $ 前缀
    modified_interface = add_dollar_prefix(interface)
    
    # 生成翻译文件
    generate_translation_files(modified_interface)
    
    # 保存修改后的 interface.json
    write_interface(interface_path, modified_interface)
    
    print("i18n 翻译文件生成完成!")
    print("已生成以下文件:")
    print("- interface_en_US.json (英文翻译模板)")
    print("- interface_zh_HK.json (繁体中文翻译模板)")
    print("- interface_zh_CN.json (简体中文翻译文件)")
    print("- 修改后的 interface.json (已添加 $ 前缀)")

if __name__ == "__main__":
    main()
