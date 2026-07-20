"""资源 pipeline 基础预检。

在调用 MaaFW load_resource 前扫描 ``resource/pipeline``，检出：
- JSON / JSONC 解析失败
- 同文件顶层节点名重复
- 跨文件顶层节点名重复（对齐 MaaFW ``key already exists``）
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import jsonc

from app.utils.logger import logger

_PIPELINE_SUFFIXES = {".json", ".jsonc"}


@dataclass(frozen=True, slots=True)
class PipelineCheckIssue:
    """单条 pipeline 预检问题。"""

    kind: str  # parse_error | duplicate_in_file | duplicate_across_files
    path: Path
    message: str
    key: str = ""
    first_path: Path | None = None


class _DupTrackingDict(dict):
    """记录构造时出现的重复 key（仅当前对象一层）。"""

    def __init__(self, *args, **kwargs):
        self.duplicates: list[str] = []
        super().__init__(*args, **kwargs)


def _object_pairs_hook(pairs: list[tuple[str, object]]) -> _DupTrackingDict:
    result = _DupTrackingDict()
    for key, value in pairs:
        if key in result:
            result.duplicates.append(key)
        result[key] = value
    return result


def _iter_pipeline_files(pipeline_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in pipeline_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in _PIPELINE_SUFFIXES:
            files.append(path)
    files.sort(key=lambda p: str(p).lower())
    return files


def _load_top_level_nodes(
    path: Path,
) -> tuple[dict[str, object] | None, list[str], str | None]:
    """解析单个 pipeline 文件，返回 (节点字典, 同文件重复key列表, 解析错误)。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [], str(exc)

    try:
        data = jsonc.loads(text, object_pairs_hook=_object_pairs_hook)
    except Exception as exc:  # jsonc.JSONDecodeError 及兼容异常
        return None, [], str(exc)

    if data is None:
        return {}, [], None
    if not isinstance(data, dict):
        return None, [], "pipeline root must be a JSON object"

    duplicates = list(getattr(data, "duplicates", []))
    # 转为普通 dict，避免后续持有自定义类型
    return dict(data), duplicates, None


def check_resource_pipeline(resource_dir: str | Path) -> list[PipelineCheckIssue]:
    """检查资源目录下 ``pipeline`` 的基础合法性。

    Args:
        resource_dir: 资源 bundle 根目录，例如 ``.../resource/base``。

    Returns:
        问题列表；空列表表示通过或无需检查（无 pipeline 目录）。
    """
    root = Path(resource_dir)
    pipeline_dir = root / "pipeline"
    if not pipeline_dir.is_dir():
        return []

    issues: list[PipelineCheckIssue] = []
    first_seen: dict[str, Path] = {}

    for path in _iter_pipeline_files(pipeline_dir):
        nodes, in_file_dups, parse_error = _load_top_level_nodes(path)
        if parse_error is not None:
            issues.append(
                PipelineCheckIssue(
                    kind="parse_error",
                    path=path,
                    message=parse_error,
                )
            )
            continue
        assert nodes is not None

        for key in in_file_dups:
            issues.append(
                PipelineCheckIssue(
                    kind="duplicate_in_file",
                    path=path,
                    key=key,
                    message=f'duplicate node "{key}" in the same file',
                )
            )

        for key in nodes:
            if key in first_seen:
                issues.append(
                    PipelineCheckIssue(
                        kind="duplicate_across_files",
                        path=path,
                        key=key,
                        first_path=first_seen[key],
                        message=(
                            f'duplicate node "{key}" '
                            f"(already defined in {first_seen[key]})"
                        ),
                    )
                )
            else:
                first_seen[key] = path

    if issues:
        logger.warning(
            "pipeline 预检发现问题: resource=%s, count=%s",
            root,
            len(issues),
        )
    return issues


def format_pipeline_issue(issue: PipelineCheckIssue) -> str:
    """格式化为单行日志文本（不含翻译前缀）。"""
    if issue.kind == "parse_error":
        return f"invalid JSON in {issue.path}: {issue.message}"
    if issue.kind == "duplicate_in_file":
        return f'duplicate node "{issue.key}" in {issue.path}'
    if issue.kind == "duplicate_across_files":
        first = issue.first_path if issue.first_path is not None else "?"
        return (
            f'duplicate node "{issue.key}" in {issue.path} '
            f"(already defined in {first})"
        )
    return issue.message
