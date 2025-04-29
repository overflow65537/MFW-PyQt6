import os
import sys
import shutil
import subprocess
import site
from setuptools import setup

# 清理之前的构建目录
def clean_build():
    build_dirs = ['dist', 'build']
    for dir in build_dirs:
        if os.path.exists(dir):
            shutil.rmtree(dir)

# 创建应用包
def build_app():
    # 配置py2app选项
    APP = ['main.py']
    
    # 获取maa的Python文件路径
    maa_py_path = os.path.join(site.getsitepackages()[0], 'maa')
    maa_py_files = []
    if os.path.exists(maa_py_path):
        for root, _, files in os.walk(maa_py_path):
            for file in files:
                if file.endswith('.py'):
                    maa_py_files.append(os.path.join(root, file))
    
    DATA_FILES = [
        'MFW_resource',
        'config',
        'dll',
        ('maa', [os.path.join(site.getsitepackages()[0], 'maa')]),
        ('maa_py', maa_py_files),  # 添加maa的Python文件
        ('MaaAgentBinary', [os.path.join(site.getsitepackages()[0], 'MaaAgentBinary')])
    ]
    
    OPTIONS = {
        'argv_emulation': True,
        'iconfile': 'MFW_resource/icon/logo.icns',
        'plist': {
            'CFBundleName': 'MFW',
            'CFBundleDisplayName': 'MFW',
            'CFBundleIdentifier': 'com.overflow65537.MFWPYQT6',
            'CFBundleVersion': sys.argv[-1],
            'NSHumanReadableCopyright': 'Copyright © 2025 Overflow65537',
            'LSMinimumSystemVersion': '12.1',
            'PyRuntimeLocations': [
                '/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/python3'  
            ]
        },
        'includes': ['PyQt6'],
        'resources': DATA_FILES,
        'frameworks': [
            os.path.join(site.getsitepackages()[0], 'PyQt6', 'Qt6', 'lib', 'QtCore.framework'),
            os.path.join(site.getsitepackages()[0], 'PyQt6', 'Qt6', 'lib', 'QtGui.framework'),
            os.path.join(site.getsitepackages()[0], 'PyQt6', 'Qt6', 'lib', 'QtWidgets.framework')
        ]
    }

    setup(
        app=APP,
        options={'py2app': OPTIONS},
        setup_requires=['py2app'],
    )

# 复制额外文件到应用包
def copy_additional_files():
    app_path = os.path.join('dist', 'MFW.app')
    contents_path = os.path.join(app_path, 'Contents')
    
    # 复制Qt插件
    qt_plugins = os.path.join(site.getsitepackages()[0], 'PyQt6', 'Qt6', 'plugins')
    if os.path.exists(qt_plugins):
        shutil.copytree(
            qt_plugins,
            os.path.join(contents_path, 'Resources', 'qt_plugins'),
            symlinks=True
        )
    
    # 复制Qt QML
    qt_qml = os.path.join(site.getsitepackages()[0], 'PyQt6', 'Qt6', 'qml')
    if os.path.exists(qt_qml):
        shutil.copytree(
            qt_qml,
            os.path.join(contents_path, 'Resources', 'qt_qml'),
            symlinks=True
        )

# 创建dmg安装包
def build_updater():
    """构建更新器"""
    updater_src = 'updater.py'
    if os.path.exists(updater_src):
        setup(
            script_args=['py2app'],
            app=[updater_src],
            options={
                'py2app': {
                    'argv_emulation': False,
                    'plist': {
                        'CFBundleName': 'MFWUpdater',
                        'CFBundleIdentifier': 'com.overflow65537.MFWUpdater'
                    }
                }
            },
            setup_requires=['py2app'],
        )

def create_dmg():
    """创建包含主程序和所有资源的DMG"""
    dmg_path = os.path.join('dist', 'MFW_Complete.dmg')
    temp_dir = os.path.join('dist', 'temp_dmg')
    
    # 创建临时目录结构
    os.makedirs(temp_dir, exist_ok=True)
    
    # 复制主程序
    shutil.copytree(
        os.path.join('dist', 'MFW.app'),
        os.path.join(temp_dir, 'MFW.app'),
        dirs_exist_ok=True
    )
    
    # 复制更新器
    updater_src = os.path.join('dist', 'MFWUpdater.app')
    if os.path.exists(updater_src):
        shutil.copytree(
            updater_src,
            os.path.join(temp_dir, 'MFWUpdater.app'),
            dirs_exist_ok=True
        )
    
    # 复制额外的资源文件
    additional_resources = ['MFW_resource', 'config', 'dll']
    for resource in additional_resources:
        if os.path.exists(resource):
            shutil.copytree(
                resource,
                os.path.join(temp_dir, resource),
                dirs_exist_ok=True
            )
    
    # 创建Applications快捷方式
    os.symlink('/Applications', os.path.join(temp_dir, 'Applications'))
    
    # 创建背景图片和布局文件
    background_src = 'MFW_resource/icon/background.png'
    if os.path.exists(background_src):
        os.makedirs(os.path.join(temp_dir, '.background'), exist_ok=True)
        shutil.copy(
            background_src,
            os.path.join(temp_dir, '.background', 'background.png')
        )
    
    # 创建DMG
    if os.path.exists(dmg_path):
        os.remove(dmg_path)
    
    subprocess.run([
        'hdiutil', 'create',
        '-volname', 'MFW',
        '-srcfolder', temp_dir,
        '-ov', dmg_path,
        '-format', 'UDZO',
        '-fs', 'HFS+',
        '-imagekey', 'zlib-level=9'
    ])
    
    # 清理临时目录
    shutil.rmtree(temp_dir)

if __name__ == '__main__':
    # 清理旧构建
    clean_build()
    
    # 构建主程序
    build_app()
    
    # 构建更新器
    build_updater()
    
    # 复制额外文件
    copy_additional_files()
    
    # 创建dmg安装包
    create_dmg()
    
    print("构建完成！完整安装包位于 dist/MFW_Complete.dmg")