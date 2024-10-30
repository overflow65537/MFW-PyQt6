<div align="center">

# PYQT-MAA
**[简体中文](./README.md) | [English](./README-en.md)**

 **[MAAFramework](https://github.com/MaaXYZ/MaaFramework)** General GUI Project Based on **[PyQT6](https://doc.qt.io/qtforpython-6)**
</div>

## Dev Environment
- Python 3.12

## Usage
- Put the MaaFramework resource folder `resource` and `interface.json` into the project root directory.
- `pip install -r requirements.txt`
- `python main.py`

## Featrues
### Custom Program Configuration
- Create `./config/custom.json`
- The file should contain the following content:
```
{
    "option1": {
        "optionname": "option1",
        "optiontype": "switch",
        "optioncontent": false,
        "text": {
            "title":"Switch",
            "content":"This is a Switch."
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
            "title":"Combox",
            "content":"This is a Combox."
        }
    },
    "option3": {
        "optionname": "option3",
        "optiontype": "lineedit",
        "optioncontent": "content3",
        "text": {
            "title":"Lineedit",
            "content":"This is a Lineedit"
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
