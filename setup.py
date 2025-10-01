from setuptools import setup
import os

# 获取项目版本信息
def get_version():
    try:
        with open('VERSION', 'r') as f:
            return f.read().strip()
    except:
        return '1.0.0'

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
        'CFBundleName': 'MFW-CFA',
        'CFBundleDisplayName': 'MFW-CFA',
        'CFBundleGetInfoString': 'MFW-CFA',
        'CFBundleIdentifier': 'com.overflow65537.MFW-CFA',
        'CFBundleVersion': get_version(),
        'CFBundleShortVersionString': get_version(),
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
    name='MFW-ChainFlow Assistant',
    version=get_version(),
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)