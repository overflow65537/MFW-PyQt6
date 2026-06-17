<!-- markdownlint-disable MD033 MD041 -->

<div align="center">

# MFW-ChainFlow Assistant

**[简体中文](./README.md) | [English](./README-en.md)**

Cross-platform GUI built with **[PySide6](https://doc.qt.io/qtforpython-6)** and **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)**, fully supporting interface v2 for orchestrating, running, and extending automation flows out of the box.
</div>

<p align="center">
  <img alt="license" src="https://img.shields.io/github/license/overflow65537/MFW-PyQt6">
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blueviolet">
  <img alt="commit" src="https://img.shields.io/github/commit-activity/m/overflow65537/MFW-PyQt6">
</p>

## Table of Contents

- [Overview](#overview)
- [Highlights](#highlights)
- [Speedrun Mode](#speedrun-mode)
- [Development Guide](#development-guide)
- [Common CLI Parameters](#common-cli-parameters)
- [External Notifications](#external-notifications)
- [Scheduling](#scheduling)
- [Hot Update](#hot-update)
- [Dynamic Custom Actions/Recognizers](#dynamic-custom-actionsrecognizers)
- [GitHub Action Build](#github-action-build)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Overview

MFW-ChainFlow Assistant provides a ready-to-use visual orchestrator for MaaFramework users, covering configuration management, task scheduling, notifications, and custom extensions to reduce automation development and ops costs.

## Highlights

- Full support for [interface v2](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/3.3-ProjectInterfaceV2%E5%8D%8F%E8%AE%AE.md) V2.4.0
- Cross-platform: Windows / Linux / macOS
- Parameterized launch: specify config ID and auto-run tasks
- External notifications: DingTalk, Lark/Feishu, SMTP, WxPusher, WeCom bot, Gotify
- Built-in scheduler: once / daily / weekly / monthly with queue or force run
- Dynamic custom actions and recognizers, with Agent support for tailored flows
- Embedded Agent: enable built-in mode via `CFA_setting.json` to automatically convert to custom loading, using the UI's internal environment for a smaller and lighter footprint
- Speedrun mode: limit runs per day/week/month with minimal intervals to avoid repeats
- Hot update: automatically enabled when `update_flag` in `CFA_setting.json` matches between resource repo and local, faster and no restart required

## Speedrun Mode

- Add a `speedrun` block under each task in `interface.json`, and set `speedrun.enabled: true` to activate the limits.
- Supports daily / weekly / monthly cycles with run counts and minimal intervals; will skip when quota is exhausted.
- Full field reference and examples: `docs/speedrun_mode.md`.

## Development Guide

- Development environment, run/debug, testing, i18n workflow, and packaging steps: [docs/development.md](docs/development.md).

## Common CLI Parameters

MFW flags go before the `--` separator; everything after is passed to Qt only.

- `--config-id <ID>`: start with the specified config ID (`--config-id=<ID>` also works)
- `--direct-run`: run tasks immediately after launch
- `--force-restart`: force-start by shutting down other MFW instances in the same directory
- `--dev`: enable developer test page

Example: `MFW.exe --direct-run --force-restart --config-id c_xxx`

## External Notifications

Supports DingTalk, Lark/Feishu, SMTP, WxPusher, WeCom bot, and Gotify; enable as needed in your configuration.

## Scheduling

Run saved configurations on once / daily / weekly / monthly cadence. Choose force start or queued execution; toggle or delete schedules directly in the list.

## Hot Update

Place `CFA_setting.json` at the resource bundle root. When the `update_flag` field matches between local and the remote repository, hot update mode is enabled—faster and requires no restart.

```json
{
  "update_flag": "1",
  "embedded": false
}
```

| Field | Required | Description |
| --- | --- | --- |
| `update_flag` | Yes | Hot-update identifier; enabled when local and remote values match |
| `embedded` | No | Agent embedded mode switch; see [Embedded Agent](#embedded-agent) below |

> Legacy compatibility: if `CFA_setting.json` is absent, falls back to `update_flag.txt` (`update_flag` only, no `embedded`).

## Dynamic Custom Actions/Recognizers

Refer to MaaFramework's [custom action/recognizer guide](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/1.1-%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B.md#%E4%BD%BF%E7%94%A8-json-%E4%BD%8E%E4%BB%A3%E7%A0%81%E7%BC%96%E7%A8%8B%E4%BD%86%E5%AF%B9%E5%A4%8D%E6%9D%82%E4%BB%BB%E5%8A%A1%E4%BD%BF%E7%94%A8%E8%87%AA%E5%AE%9A%E4%B9%89%E9%80%BB%E8%BE%91):

1. Use Python 3.12 for custom actions/recognizers.
2. If third-party deps are required, install them into the `_internal` directory.
3. Declare custom objects in `custom.json`, and point to it via the `custom` key in `interface.json` (`{custom_path}` defaults to the repo's `custom/`).
4. Reference the custom names in your pipeline.

Example `custom.json` snippet:

```json
{
  "ActionName1": {
    "file_path": "{custom_path}/any/path/action1.py",
    "class": "ActionClass1",
    "type": "action"
  },
  "RecognizerName1": {
    "file_path": "{custom_path}/any/path/recognizer1.py",
    "class": "RecognizerClass1",
    "type": "recognition"
  }
}
```

Referencing in pipeline:

```json
"MyCustomTask": {
  "recognition": "Custom",
  "custom_recognition": "RecognizerName1",
  "action": "Custom",
  "custom_action": "ActionName1"
}
```

Custom class example:

```python
class ActionClass1(CustomAction):
    def apply(self, context, ...):
        image = context.tasker.controller.cached_image
        # process the image and return your result
```

More examples: [MAA_Punish/assets](https://github.com/overflow65537/MAA_Punish/tree/main/assets).

### Embedded Agent

Set `"embedded": true` in `CFA_setting.json` to automatically convert the agent to custom loading mode. This approach runs within the UI's internal environment without a separate process, resulting in lower resource usage and faster startup. After a hot update, this value is synced to `agent.embedded` in `interface.json`.

Example `CFA_setting.json`:

```json
{
  "update_flag": "1",
  "embedded": true
}
```

Keep the agent entry in `interface.json`, for example:

```json
{
  "agent": {
    "child_args": ["{PROJECT_DIR}/agent/main.py"]
  }
}
```

When embedded mode is enabled, the system will automatically:

1. Copy the agent entry directory
2. Generate the corresponding `custom.json` configuration
3. Keep the `agent` field and inject an additional `custom` field for generated runtime loading

## GitHub Action Build

1. Replace `MaaXXX` with your project name in `deploy/install.yml`.
2. Commit and push to `.github/workflows` in your GitHub repo.
3. Push a new release/tag to trigger the automated build.

## License

**MFW-PyQt6** is open source under **[GPL-3.0 License](./LICENSE)**.

## Acknowledgments

### Open Source Projects

- **[PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)**\
    A fluent design widgets library based on C++ Qt/PyQt/PySide.
- **[MaaFramework](https://github.com/MaaAssistantArknights/MaaFramework)**\
    An image-recognition-based automation framework.
- **[MirrorChyan](https://github.com/MirrorChyan/docs)**\
    Mirror-chan update service.
- **[AutoMAA](https://github.com/DLmaster361/AUTO_MAA)**\
    A MAA plugin for multi-account management and automation.

### Contributors

<a href="https://github.com/overflow65537/PYQT-MAA/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=overflow65537/PYQT-MAA" alt="Project contributors"/>
</a>
