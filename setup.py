from setuptools import setup
import os
import re

# 获取项目版本信息并规范化版本号格式
def get_version():
    try:
        with open('VERSION', 'r') as f:
            version = f.read().strip()
        
        # 规范化版本号格式
        # 移除v前缀，将-ci.转换为.post
        version = re.sub(r'^v', '', version)  # 移除v前缀
        version = re.sub(r'-ci\.(\d+)', r'.post\1', version)  # 将-ci.251001转换为.post251001
        version = re.sub(r'-([a-f0-9]+)$', r'.dev\1', version)  # 将-2fe0eb2转换为.dev2fe0eb2
        
        # 验证版本号格式
        if re.match(r'^\d+\.\d+\.\d+(\.post\d+)?(\.dev[a-f0-9]+)?$', version):
            return version
        else:
            # 如果格式仍然不正确，使用默认版本
            print(f"Warning: Version format '{version}' is not standard, using default")
            return '2.4.15'
    except:
        return '2.4.15'

# 获取原始版本号用于plist（macOS可以接受更灵活的版本格式）
def get_plist_version():
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except:
        return '2.4.15'

# 获取项目依赖
def get_requirements():
    try:
        with open('requirements.txt', 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except:
        return []

APP = ['main.py']
DATA_FILES = []

# 包含资源文件
def include_resources():
    resources = []
    
    # 包含i18n翻译文件
    i18n_dir = 'MFW_resource/i18n'
    if os.path.exists(i18n_dir):
        for file in os.listdir(i18n_dir):
            if file.endswith('.ts') or file.endswith('.qm'):
                resources.append(os.path.join(i18n_dir, file))
    
    # 包含其他资源文件
    resource_dirs = ['MFW_resource/images', 'MFW_resource/fonts', 'MFW_resource/styles']
    for dir_path in resource_dirs:
        if os.path.exists(dir_path):
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    resources.append(os.path.join(root, file))
    
    return resources

DATA_FILES = include_resources()

OPTIONS = {
    'argv_emulation': False,  # 禁用argv模拟，避免启动问题
    'plist': {
        'CFBundleName': 'MFW',
        'CFBundleDisplayName': 'MFW',
        'CFBundleGetInfoString': 'MFW - 链程助手',
        'CFBundleIdentifier': 'com.mfw.chainflow.assistant',
        'CFBundleVersion': get_plist_version(),  # macOS可以使用原始版本号
        'CFBundleShortVersionString': get_plist_version(),  # macOS可以使用原始版本号
        'NSHumanReadableCopyright': 'Copyright © 2024 MFW. All rights reserved.',
        'LSMinimumSystemVersion': '10.15.0',
        'CFBundleDevelopmentRegion': 'zh_CN',
        'CFBundleDocumentTypes': [],
        'CFBundleURLTypes': [],
    },
    'packages': get_requirements(),
    'includes': ['app', 'MFW_resource'],
    'excludes': ['tkinter', 'PyQt5', 'PyQt6.QtWebEngine', 'PyQt6.QtWebEngineCore'],
    'resources': DATA_FILES,
    'iconfile': 'MFW_resource/images/icon.icns' if os.path.exists('MFW_resource/images/icon.icns') else None,
    'frameworks': [],
    'site_packages': True,
}

setup(
    name='MFW',
    version=get_version(),  # 使用规范化的版本号
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)