#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
from pathlib import Path
import re
import shutil

def normalize_version(version):
    """
    规范化版本号格式，使其符合Python打包要求
    """
    # 移除v前缀
    version = re.sub(r'^v', '', version)
    
    # 将-ci.转换为.post
    version = re.sub(r'-ci\.(\d+)', r'.post\1', version)
    
    # 将git commit hash转换为数字（取前8位并转换为整数）
    match = re.search(r'-([a-f0-9]+)$', version)
    if match:
        commit_hash = match.group(1)
        # 取前8位并转换为整数（避免十六进制字符）
        commit_num = int(commit_hash[:8], 16) if len(commit_hash) >= 8 else int(commit_hash + '0' * (8 - len(commit_hash)), 16)
        version = re.sub(r'-([a-f0-9]+)$', f'.dev{commit_num}', version)
    
    # 验证版本号格式是否符合PEP 440
    if re.match(r'^\d+\.\d+\.\d+(\.post\d+)?(\.dev\d+)?$', version):
        return version
    else:
        # 如果格式仍然不正确，使用默认版本
        print(f"Warning: Version format '{version}' is not standard, using default")
        return '2.4.15'

def build_app(platform, arch, version):
    """
    使用py2app构建应用
    """
    # 规范化版本号
    normalized_version = normalize_version(version)
    print(f"Building MFW for {platform}-{arch} version {version} (normalized: {normalized_version})")
    
    # 设置版本信息
    with open('VERSION', 'w') as f:
        f.write(version)  # 写入原始版本号
    
    try:
        # 清理之前的构建
        if os.path.exists('dist'):
            shutil.rmtree('dist')
        if os.path.exists('build'):
            shutil.rmtree('build')
            
        # 执行py2app构建
        if platform == 'macos':
            result = subprocess.run([sys.executable, 'setup.py', 'py2app'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Build failed: {result.stderr}")
                return False
                
            print("Build completed successfully!")
            
            # 测试应用
            app_path = Path('dist/MFW.app')
            if app_path.exists():
                print(f"Application built at: {app_path}")
                
                # 创建DMG包
                dmg_name = f"MFW-{version}-{arch}.dmg"
                dmg_cmd = [
                    'hdiutil', 'create', '-volname', 'MFW',
                    '-srcfolder', 'dist/MFW.app', '-ov', '-format', 'UDZO',
                    f'dist/{dmg_name}'
                ]
                
                dmg_result = subprocess.run(dmg_cmd, capture_output=True, text=True)
                if dmg_result.returncode == 0:
                    print(f"DMG package created: dist/{dmg_name}")
                else:
                    print(f"DMG creation failed: {dmg_result.stderr}")
                    
            return True
            
        else:
            print(f"Platform {platform} is not supported for py2app builds")
            return False
            
    except Exception as e:
        print(f"Build error: {e}")
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build MFW with py2app')
    parser.add_argument('platform', help='Target platform (macos only)')
    parser.add_argument('arch', help='Target architecture')
    parser.add_argument('version', help='Application version')
    
    args = parser.parse_args()
    
    success = build_app(args.platform, args.arch, args.version)
    sys.exit(0 if success else 1)