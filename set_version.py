import os
import sys
from pathlib import Path
import plistlib
from app.common.__version__ import __version__

# 获取版本号
version = __version__

# 找到生成的 Info.plist 文件
app_path = Path(sys._MEIPASS) / "MFW.app" / "Contents" # type: ignore
plist_path = app_path / "Info.plist"

# 读取并修改 Info.plist
with open(plist_path, 'rb') as f:
    plist = plistlib.load(f)

plist['CFBundleShortVersionString'] = version
plist['CFBundleVersion'] = version

# 写回修改后的 Info.plist
with open(plist_path, 'wb') as f:
    plistlib.dump(plist, f)
