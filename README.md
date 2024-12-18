<div align="center">

# MFW-PyQt6
**[简体中文](./README.md) | [English](./README-en.md)**

基于 **[PyQT6](https://doc.qt.io/qtforpython-6)** 的 **[MAAFramework](https://github.com/MaaXYZ/MaaFramework)** 通用 GUI 项目
</div>

## 开发环境
- Python 3.12

## 使用方法
- `pip install -r requirements.txt`
- `python main.py`

## 功能说明
### 多配置启动
- 在计划任务界面点击资源的添加按钮即可添加资源
- 每个资源可以有多个配置,互相独立
- 结束后操作可以选择启动其他资源中的某项配置文件
- 配合启动后执行任务可以实现多资源的无缝启动

### 计划任务(可能要鸽)
- 计划任务界面可以设置任务的启动时间，循环时间来启动资源中的某项配置

### 外部通知
- 目前支持 钉钉,飞书,SMTP,WxPusher 四种通知方式

### 更新资源
- 添加资源时如果填写了更新地址,可以进行一键更新
- **要求项目发行版内包含有update.zip**

### Custom 程序配置
- 创建 `./config/custom.json`
- 内容为
```
{
    "option1": {
        "optionname": "option1",
        "optiontype": "switch",
        "optioncontent": false,
        "text": {
            "title": "开关",
            "content": "这是一个开关"
        }
    },
    "option2": {
        "optionname": "option2",
        "optiontype": "combox",
        "optioncontent": [
            "content1",
            "content2",
            "content3"
        ],
        "text": {
            "title": "下拉框",
            "content": "这是一个下拉框"
        }
    },
    "option3": {
        "optionname": "option3",
        "optiontype": "lineedit",
        "optioncontent": "content3",
        "text": {
            "title": "输入框",
            "content": "这是一个输入框"
        }
    }
}
```
- 处理后的数据会保存至 `./config/custom_config.json` 以供custom程序读取。

## 许可证
**MFW-PyQt6** 使用 **[GPL-3.0 许可证](./LICENSE)** 开源。

## 致谢
### 开源项目
- **[PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)**\
    A fluent design widgets library based on C++ Qt/PyQt/PySide. Make Qt Great Again.
- **[MaaFramework](https://github.com/MaaAssistantArknights/MaaFramework)**\
    基于图像识别的自动化黑盒测试框架。

### 开发者
感谢所有为 **MFW-PyQt6** 做出贡献的开发者。

<a href="https://github.com/overflow65537/PYQT-MAA/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=overflow65537/PYQT-MAA&max=1000" />
</a>
