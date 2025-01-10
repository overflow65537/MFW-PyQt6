<div align="center">

# MFW-PyQt6
**[简体中文](./README.md) | [English](./README-en.md)**

基于 **[PyQT6](https://doc.qt.io/qtforpython-6)** 的 **[MAAFramework](https://github.com/MaaXYZ/MaaFramework)** 通用 GUI 项目
</div>

## 开发环境
- Python 3.12

## 使用方法
### 直接使用
- `pip install -r requirements.txt`
- `python main.py`

### 使用GitHub action 自动构建
- 将`depoly\deploy.py` 中的项目名和项目地址修改为你的项目名和项目地址并上传至`GitHub仓库根目录`
- 将`deploy\install.yml` 中MaaXXX修改为你的项目名并上传至GitHub仓库的`.github/workflows`目录
- 推送新版本

## 功能说明
### 多配置启动
- 在计划任务界面点击资源的添加按钮即可添加资源
- 每个资源可以有多个配置,互相独立
- 结束后操作可以选择启动其他资源中的某项配置文件
- 配合启动后执行任务可以实现多资源的无缝启动

### 参数启动
- -r参数可接受资源名称 例如 `python main.py -r resource1`或者 `main.exe -r resource1`
- -c参数可接受配置文件名称 例如 `python main.py -c config1`或者 `main.exe -c config1`
- -d参数可以直接启动 例如 `python main.py -d`或者 `main.exe -d`

### 外部通知
- 目前支持 钉钉,飞书,SMTP,WxPusher 四种通知方式

### 更新资源
- 添加资源时如果填写了更新地址,可以进行一键更新

### 动态加载自定义动作/识别器
- 什么是[自定义动作/识别器](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/1.1-%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B.md#%E4%BD%BF%E7%94%A8-json-%E4%BD%8E%E4%BB%A3%E7%A0%81%E7%BC%96%E7%A8%8B%E4%BD%86%E5%AF%B9%E5%A4%8D%E6%9D%82%E4%BB%BB%E5%8A%A1%E4%BD%BF%E7%94%A8%E8%87%AA%E5%AE%9A%E4%B9%89%E9%80%BB%E8%BE%91)
- 将自定义动作/识别器文件按照要求命名和放置
- 要求的结构:[这是例子](https://github.com/overflow65537/MAA_Punish/tree/main/assets)
```
资源文件夹/custom/
├── action/
│   ├── 动作1
│   │    └── main.py
│   └── 动作2
│        └── main.py
└── Recognition/
    ├── 识别器1
    │    └── main.py
    └── 识别器2
         └── main.py
```
- 其中,动作1,动作2,识别器1,识别器2为在pipeline中所使用的名字,比如
```
"我的自定义任务": {
        "recognition": "Custom",
        "custom_recognition": "识别器1",
        "action": "Custom",
        "custom_action": "动作1"
    }
```
- main.py中要求对象名和文件夹相同,比如
```
  class 识别器1(CustomRecognition):
    def analyze(context, ...):
        # 获取图片，然后进行自己的图像操作
        image = context.tasker.controller.cached_image
        # 返回图像分析结果
        return AnalyzeResult(box=(10, 10, 100, 100))

 ```


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
