常用启动参数（MFW 开关写在分隔符 `--` 之前；之后仅传给 Qt）：

- `--config-id <ID>`（或 `--config-id=<ID>`）：启动后切换到指定配置
- `--direct-run`：启动后直接运行任务流
- `--dev`：显示测试页面（开发调试开关）
- `--force-restart`：强制重启同目录下已有实例

示例：

```powershell
python main.py --config-id default --direct-run --dev
python main.py --config-id=default --direct-run -- -platform windows:darkmode=1
MFW.exe --direct-run --force-restart --config-id c_08b08298fcf340d8a028ee63503125e2
```

查看完整说明：`python main.py --help`
