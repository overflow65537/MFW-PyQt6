<div align="center">

# MFW-PyQt6
**[简体中文](./README.md) | [English](./README-en.md)**

A general GUI project of **[MAAFramework](https://github.com/MaaXYZ/MaaFramework)** based on **[PyQT6](https://doc.qt.io/qtforpython-6)**.

</div>

## Development Environment
- Python 3.12

## Usage Method
### Direct Usage
- `pip install -r requirements.txt`
- `python main.py`

### Automatic Build with GitHub Actions
- Change the project name and project address in `depoly\deploy.py` to your project name and project address, and upload it to the root directory of your `GitHub repository`.
- Change MaaXXX to your project name in `deploy\install.yml`, and upload it to the `.github/workflows` directory of your GitHub repository.
- Push the new version.

## Feature Description
### Multi-configuration Launch
- Click the add button for resources in the task scheduling interface to add resources.
- Each resource can have multiple configurations, which are independent of each other.
- After the operation is finished, you can choose to start a configuration file from another resource.
- With the start and execute task function, seamless launch for multiple resources can be achieved.

### Parameter Launch
- The -r parameter accepts resource names, e.g., `python main.py -r resource1` or `main.exe -r resource1`.
- The -c parameter accepts configuration file names, e.g., `python main.py -c config1` or `main.exe -c config1`.
- The -d parameter allows direct startup, e.g., `python main.py -d` or `main.exe -d`.

### External Notifications
- Currently supports DingTalk, FeiShu, SMTP, and WxPusher notification methods.

### Update Resource
- If an update address is filled when adding resources, one-click updates can be performed.

### Custom Program Configuration
- Create `./config/custom.json`.
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
  <img src="https://contrib.rocks/image?repo=overflow65537/PYQT-MAA&max=1000" />
</a>
