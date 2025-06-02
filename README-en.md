<!-- markdownlint-disable MD033 MD041 -->

<div align="center">

# MFW-ChainFlow Assistant

**[简体中文](./README.md) | [English](./README-en.md)**

Universal GUI project for **[MAAFramework](https://github.com/MaaXYZ/MaaFramework)** based on **[PySide6](https://doc.qt.io/qtforpython-6)**
</div>

<p align="center">
  <img alt="license" src="https://img.shields.io/github/license/overflow65537/MFW-PyQt6">
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blueviolet">
  <img alt="commit" src="https://img.shields.io/github/commit-activity/m/overflow65537/MFW-PyQt6">
</p>

## Development Environment

- Python 3.12

## Usage

### Direct Usage

- `pip install -r requirements.txt`
- `python main.py`

### Using GitHub Actions for Auto Deployment

- Modify the project name and URL in `deploy/deploy.py` and upload to the GitHub repository root
- Rename MaaXXX in `deploy/install.yml` to your project name and upload to `.github/workflows` directory
- Push new releases

## Features

### Multi-configuration Launch

- Click the add button in Scheduled Tasks interface to add resources
- Each resource can have multiple independent configurations
- Post-completion actions can trigger configurations from other resources
- Combined with post-execution tasks to achieve seamless multi-resource startup

### Parameter Launch

- -r parameter accepts resource names e.g. `python main.py -r resource1` or `MFW.exe -r resource1`
- -c parameter accepts configuration names e.g. `python main.py -c config1` or `MFW.exe -c config1`
- -d parameter starts task immediately after launch e.g. `python main.py -d` or `MFW.exe -d`

### Version Locking

- Add `MFW_min_req_version` key in `interface.json` with MFW version number:

```json
"MFW_min_req_version": "1.5.4"
```

- Updates will be blocked if new resources require higher MFW version

### Speedrun Mode

- Enable in Settings to skip tasks already completed in current cycle
- Developers can set operation cycles in interface file:

```json
{
    "task": [
        {
            "name": "Daily Tasks",
            "entry": "Daily Tasks",
            "periodic": 1,
            "daily_start": 4
        },
        {
            "name": "Weekly Tasks",
            "entry": "Weekly Tasks",
            "periodic": 2,
            "weekly_start": 2,
            "daily_start": 4
        }
    ]
}
```

### External Notifications

- Currently supports DingTalk, Feishu, SMTP, and WxPusher

### `doc` Protocol

#### Use markup like `[color:red]Text[/color]` for styling

#### Supported Markup

- `[color:color_name]`: Text color
- `[size:font_size]`: Font size
- `[b]`: Bold
- `[i]`: Italic
- `[u]`: Underline
- `[s]`: Strikethrough
- `[align:left/center/right]`: Text alignment (must be used on separate lines)

### Task Notifications

- Requires enabling node's Focus feature
- Format using doc protocol:

```json
{
    "task": {
        "focus": {
            "start": "[size:15][color:gray]Task start notification[/color][/size]",
            "succeeded": "[size:15][color:green]Task success notification[/color][/size]"
        }
    }
}
```

### Custom Action/Recognizer Integration

#### Fixed Location Method

- Requires Python 3.12 for custom components
- Third-party libraries must be installed in `_internal` folder
- Create `costom.json` in custom folder:

```json
{
    "CustomAction1": {
        "file_path": "{custom_path}/actions/action1.py",
        "class": "CustomActionClass",
        "type": "action"
    }
}
```

- Use in pipeline:

```json
"MyCustomTask": {
    "recognition": "Custom",
    "custom_recognition": "CustomRecognizer1",
    "action": "Custom",
    "custom_action": "CustomAction1"
}
```

## License

**MFW-PyQt6** is open source under **[GPL-3.0 License](./LICENSE)**

## Acknowledgments

### Open Source Projects

- **[PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)**
- **[MaaFramework](https://github.com/MaaAssistantArknights/MaaFramework)**
- **[MirrorChyan](https://github.com/MirrorChyan/docs)**
- **[AutoMAA](https://github.com/DLmaster361/AUTO_MAA)**

### Contributors

<a href="https://github.com/overflow65537/PYQT-MAA/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=overflow65537/PYQT-MAA" alt="Project contributors"/>
</a>
