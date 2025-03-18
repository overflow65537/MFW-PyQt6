<!-- markdownlint-disable MD033 MD041 -->

<div align="center">

# MFW-PyQt6

**[简体中文](./README.md) | [English](./README-en.md)**

基于 **[PyQT6](https://doc.qt.io/qtforpython-6)** 的 **[MAAFramework](https://github.com/MaaXYZ/MaaFramework)** 通用 GUI 项目
</div>

<p align="center">
  <img alt="license" src="https://img.shields.io/github/license/overflow65537/MFW-PyQt6">
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blueviolet">
  <img alt="commit" src="https://img.shields.io/github/commit-activity/m/overflow65537/MFW-PyQt6">
</p>

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

- -r参数可接受资源名称 例如 `python main.py -r resource1`或者 `MFW.exe -r resource1`
- -c参数可接受配置文件名称 例如 `python main.py -c config1`或者 `MFW.exe -c config1`
- -d参数可以在运行后直接启动任务 例如 `python main.py -d`或者 `MFW.exe -d`

### 版本锁定

- 在`interface.json`文件中添加`MFW_min_req_version`键,值为MFW的版本号

```json
"MFW_min_req_version": "1.5.4"
```

- 添加后,如果MFW在更新时发现新资源中`MFW_min_req_version`的值大于当前MFW的版本号,则会停止更新并提示原因

### 速通模式

- 在设置中可以启用`速通模式`
- 启用后会跳过周期内已经运行过一次的任务
- 运行周期为资源开发者设置
- 如果设置了全局on_error(default_pipeline.json),需要打开对应node的`focus`为`True`,任务进入on_error后会显示失败,且不记录时间
- 在interface文件中,格式为:

```json
{
    "task": [
        {
            "name": "每日任务",
            "entry": "每日任务",
            "periodic": 1,      //每日任务
            "daily_start": 4    //每天4点开始
        },
        {
            "name": "每周任务",
            "entry": "每周任务",
            "periodic": 2,     //每周任务
            "weekly_start": 2, //每周二开始
            "daily_start": 4   //每天4点开始
        },
        {
            "name": "正常任务",
            "entry": "正常任务"
        }
    ]
}
```

### 外部通知

- 目前支持 钉钉,飞书,SMTP,WxPusher 四种通知方式

### Focus通知

- 需要启用对应node的`Focus`功能
- 在`pipeline`文件夹同级目录下新建`focus_msg.json`文件
- 格式为

```json
{
    "node名": {
        "focus_tip": "任务执行前显示在右侧的内容",
        "focus_tip_color": "#000000",
        "focus_succeeded": ["任务执行成功后显示在右侧的内容", "成功"],
        "focus_succeeded_color": ["(0,255,0)", "(0,255,0,50)"],
        "focus_failed": "任务执行失败后显示在右侧的内容",
        "focus_failed_color": "red"
    }
}
```

- 其中`node名`为pipeline中的节点名`
- 如果希望通过`option`来控制`focus`的显示,可以在`option`-`cases`中的对应选项内添加`focus_msg_override`字段
- 格式为

```json
{
      "option": {
        "选项组": {
            "cases": [
                {
                    "name": "选项",
                    "pipeline_override": {},
                    "focus_msg_override": {
                        "node名": {
                            "focus_tip": "任务执行前显示在右侧的内容",
                            "focus_tip_color": "#000000",
                            "focus_succeeded": ["任务执行成功后显示在右侧的内容", "成功"],
                            "focus_succeeded_color": ["(0,255,0)", "(0,255,0,50)"],
                            "focus_failed": "任务执行失败后显示在右侧的内容",
                            "focus_failed_color": "red"
                        }
                    }
                }
            ]
        }
    }
}
```

### 动态加载自定义动作/识别器

#### 固定位置方法

- 什么是[自定义动作/识别器](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/1.1-%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B.md#%E4%BD%BF%E7%94%A8-json-%E4%BD%8E%E4%BB%A3%E7%A0%81%E7%BC%96%E7%A8%8B%E4%BD%86%E5%AF%B9%E5%A4%8D%E6%9D%82%E4%BB%BB%E5%8A%A1%E4%BD%BF%E7%94%A8%E8%87%AA%E5%AE%9A%E4%B9%89%E9%80%BB%E8%BE%91)
- 要求自定义动作/识别器使用python3.12
- 如果自定义动作/识别器中含有第三方库,需要将第三方库安装到`_internal`(windows和Macos)或者`MFW-PyQt6根目录`(linux)
- 将自定义动作/识别器文件按照要求命名和放置
- 要求的结构:[这是例子](https://github.com/overflow65537/MAA_SnowBreak/tree/main/assets)

```File Tree
项目文件夹/custom/
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

```json
"我的自定义任务": {
        "recognition": "Custom",
        "custom_recognition": "识别器1",
        "action": "Custom",
        "custom_action": "动作1"
    }
```

- main.py中要求对象名和文件夹相同,比如

```python
  class 识别器1(CustomRecognition):
    def analyze(context, ...):
        # 获取图片，然后进行自己的图像操作
        image = context.tasker.controller.cached_image
        # 返回图像分析结果
        return AnalyzeResult(box=(10, 10, 100, 100))

 ```

#### 配置文件方法

- 编写`costom.json`并放置于custom文件夹内
- 这是一个[例子](https://github.com/overflow65537/MAA_Punish/tree/main/assets)
- 内容为

```json
{
        "动作名字1": {
            "file_path": "{custom_path}/任意位置/任意名字_动作1.py",
            "class": "动作对象1",
            "type": "action"
        },
        "动作名字2": {
            "file_path": "{custom_path}/任意位置/任意名字_动作1.py",
            "class": "动作对象2",
            "type": "action"
        },
        "识别器名字1": {
            "file_path": "{custom_path}/任意位置/任意名字_识别器1.py",
            "class": "识别器对象1",
            "type": "recognition"
        },
        "识别器名字2": {
            "file_path": "{custom_path}/任意位置/任意名字_识别器2.py",
            "class": "识别器对象2",
            "type": "recognition"
        }
    }
```

- 其中,动作名字1,动作名字2,识别器名字1,识别器名字2为在pipeline中所使用的名字,比如
-

```json
"我的自定义任务": {
        "recognition": "Custom",
        "custom_recognition": "识别器名字1",
        "action": "Custom",
        "custom_action": "动作名字1"
    }

```

- 动作对象1,动作对象2,识别器对象1,识别器对象2为python文件中定义的对象名,比如

```python
  class 动作对象1(CustomAction):
    def apply(context,...):
        # 获取图片，然后进行自己的图像操作
        image = context.tasker.controller.cached_image
        # 返回图像分析结果

- custom路径中的{custom_path}为MFW-PyQt6根目录中的custom文件夹
### Custom 程序配置
```

- 创建 `./config/custom.json`
- 内容为

```json
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
- **[MirrorChyan](https://github.com/MirrorChyan/docs)**\
    Mirror酱更新服务

### 开发者

感谢所有为 **MFW-PyQt6** 做出贡献的开发者。

<a href="https://github.com/overflow65537/PYQT-MAA/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=overflow65537/PYQT-MAA&max=1000" alt="Contributors to MFW-PyQt6"/>
</a>
