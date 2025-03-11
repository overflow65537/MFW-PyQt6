<!-- markdownlint-disable MD033 MD041 -->

<div align="center">

# MFW-PyQt6

**[Simplified Chinese](./README.md) | [English](./README-en.md)**

A general-purpose GUI project for **[MAAFramework](https://github.com/MaaXYZ/MaaFramework)** based on **[PyQT6](https://doc.qt.io/qtforpython-6)**
</div>

## Development Environment

- Python 3.12

## Usage

### Direct Use

- `pip install -r requirements.txt`
- `python main.py`

### Using GitHub Actions for Automatic Building

- Modify the project name and project address in `depoly\deploy.py` to your project name and project address, and upload it to the `GitHub repository root directory`
- Modify MaaXXX in `deploy\install.yml` to your project name and upload it to the `.github/workflows` directory of the GitHub repository
- Push a new version

## Feature Description

### Multi-Configuration Startup

- Click the add button for resources in the scheduled task interface to add resources
- Each resource can have multiple configurations, independent of each other
- The operation after completion can choose to start a certain configuration file in other resources
- Combined with the task executed after startup, seamless startup of multiple resources can be achieved

### Parameter Startup

- The `-r` parameter can accept the resource name, for example `python main.py -r resource1` or `MFW.exe -r resource1`
- The `-c` parameter can accept the configuration file name, for example `python main.py -c config1` or `MFW.exe -c config1`

### External Notifications

- Currently supports four notification methods: DingTalk, Feishu, SMTP, and WxPusher

### Focus Notification

- Create a new focus_msg.json file in the same directory as the pipeline folder.
- The format is as follows:

```json
{
    "Node Name": {
        "focus_tip": "Content to be displayed on the right before task execution",
        "focus_tip_color": "#000000",
        "focus_succeeded": ["Content to be displayed on the right after successful task execution", "Success"],
        "focus_succeeded_color": ["(0,255,0)", "(0,255,0,50)"],
        "focus_failed": "Content to be displayed on the right after task execution fails",
        "focus_failed_color": "red"
    }
}

```

- Here, the Node Name refers to the node name in the pipeline.

### Dynamic Loading of Custom Actions/Recognizers

- What is a [Custom Action/Recognizer](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/1.1-%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B.md#%E4%BD%BF%E7%94%A8-json-%E4%BD%8E%E4%BB%A3%E7%A0%81%E7%BC%96%E7%A8%8B%E4%BD%86%E5%AF%B9%E5%A4%8D%E6%9D%82%E4%BB%BB%E5%8A%A1%E4%BD%BF%E7%94%A8%E8%87%AA%E5%AE%9A%E4%B9%89%E9%80%BB%E8%BE%91)
- Requires custom actions/recognizers to use Python 3.12
- If the custom action/recognizer contains third-party libraries, the third-party libraries need to be installed in `_internal` (Windows and macOS) or the `MFW-PyQt6 root directory` (Linux)
- Name and place the custom action/recognizer files as required
- Required structure: [Here is an example](https://github.com/overflow65537/MAA_Punish/tree/main/assets)

```File Tree
Project Folder/custom/
├── action/
│   ├── Action1
│   │    └── main.py
│   └── Action2
│        └── main.py
└── Recognition/
    ├── Recognizer1
    │    └── main.py
    └── Recognizer2
         └── main.py
```

- Among them, Action1, Action2, Recognizer1, Recognizer2 are the names used in the pipeline, for example

```json


### Custom Program Configuration

- Create `./config/custom.json`.
- The content should be:

```json
"my_custom_task": {
        "recognition": "Custom",
        "custom_recognition": "Recognizer1",
        "action": "Custom",
        "custom_action": "Action1"
    }

```

- The object name in main.py is required to be the same as the folder name, for example

```python
  class Recognizer1(CustomRecognition):
    def analyze(context, ...):
        # Get the image, then perform your own image operations
        image = context.tasker.controller.cached_image
        # Return the image analysis result
        return AnalyzeResult(box=(10, 10, 100, 100))
```

### Custom Program Configuration

- Create ```./config/custom.json```.
- The content should be:

```json
{
    "option1": {
        "optionname": "option1",
        "optiontype": "switch",
        "optioncontent": false,
        "text": {
            "title": "Switch",
            "content": "This is a switch"
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
            "title": "Combobox",
            "content": "This is a combobox"
        }
    },
    "option3": {
        "optionname": "option3",
        "optiontype": "lineedit",
        "optioncontent": "content3",
        "text": {
            "title": "Lineedit",
            "content": "This is a lineedit"
        }
    }
}
```

- The processed data will be saved to `./config/custom_config.json` for custom programs to read.

## License

**PyQt-MAA** is licensed under **[GPL-3.0 License](./LICENSE)**.

## Acknowledgments

### Open Source Libraries

- **[PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)**\
    A fluent design widgets library based on C++ Qt/PyQt/PySide. Make Qt Great Again.
- **[MaaFramework](https://github.com/MaaAssistantArknights/MaaFramework)**\
    An automation black-box testing framework based on image recognition

### Developers

Thanks to the following developers for their contributions to PyQt-MAA.

<a href="https://github.com/overflow65537/PYQT-MAA/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=overflow65537/PYQT-MAA&max=1000" alt="Contributors to MFW-PyQt6"/>
</a>
