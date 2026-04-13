#!/usr/bin/env python3
"""
读取 app/i18n 下的 Qt Linguist .ts 文件，调用 DeepSeek Chat API 翻译 <source> 并写回 <translation>。

启动时从仓库根目录的 .llm.txt 读取 API Token（整文件 strip 后作为 token，或首行非空行）。

用法示例:
  python tools/llm_translate_ts.py
  python tools/llm_translate_ts.py --filter all
  python tools/llm_translate_ts.py --files app/i18n/i18n.zh_TW.ts --dry-run
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import threading
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

# 繁体仅使用 zh_TW .ts；与模型说明中「港台通用」风格一致
TRADITIONAL_CHINESE_HINT = (
    "繁体中文（港台通用）：采用繁体字与两岸三地用户都能理解的界面用语，"
    "避免仅限单一地区才通行的词汇；技术词可保留常见英文或业界通用写法"
)

LANGUAGE_HINTS: dict[str, str] = {
    "zh_CN": "简体中文（中国大陆），用词自然，符合软件界面习惯",
    "zh_TW": TRADITIONAL_CHINESE_HINT,
    "ja_JP": "日语，礼貌、简洁的软件 UI 用语",
    "ko_KR": "韩语，简洁的软件 UI 用语",
    "en_US": "美式英语，简洁的软件 UI 用语",
    "en_GB": "英式英语，简洁的软件 UI 用语",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_api_token(root: Path) -> str:
    path = root / ".llm.txt"
    if not path.is_file():
        raise SystemExit(
            f"未找到 {path}，请在仓库根目录创建该文件并写入 DeepSeek API Token。"
        )
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise SystemExit(f"{path} 为空，请写入 API Token。")
    for line in raw.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    raise SystemExit(f"{path} 中没有有效的 Token 行。")


def element_plain_text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return "".join(el.itertext())


def target_language_prompt(lang: str) -> str:
    return LANGUAGE_HINTS.get(lang, f"目标语言代码为 {lang}，请输出自然、符合软件界面习惯的译文")


def should_translate(
    translation: ET.Element,
    filter_mode: str,
    skip_vanished: bool,
) -> bool:
    if skip_vanished and translation.get("type") == "vanished":
        return False
    t = translation.get("type")
    text = (translation.text or "").strip()
    if filter_mode == "all":
        return True
    if filter_mode == "unfinished":
        return t == "unfinished"
    if filter_mode == "empty":
        return not text
    if filter_mode == "both":
        return t == "unfinished" or not text
    raise ValueError(f"未知 filter: {filter_mode}")


def strip_code_fence(s: str) -> str:
    s = s.strip()
    m = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", s, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return s


def split_translation_entries_into_batches(
    entries: list[tuple[ET.Element, str]],
    max_items: int,
    max_chars: int,
) -> list[list[tuple[ET.Element, str]]]:
    """
    将待译条目切成多批，兼顾「条数上限」与「字符数上限」，减少 API 调用次数、降低重复 system prompt 开销。
    max_chars<=0 时仅按条数切分。
    """
    batches: list[list[tuple[ET.Element, str]]] = []
    current: list[tuple[ET.Element, str]] = []
    current_chars = 0

    def flush() -> None:
        nonlocal current, current_chars
        if current:
            batches.append(current)
            current = []
            current_chars = 0

    for trans_el, s in entries:
        l = len(s)
        if max_chars > 0 and l > max_chars:
            flush()
            batches.append([(trans_el, s)])
            continue
        if current and (
            len(current) >= max_items
            or (max_chars > 0 and current_chars + l > max_chars)
        ):
            flush()
        current.append((trans_el, s))
        current_chars += l
    flush()
    return batches


def parse_translations_json(content: str, expected: int) -> list[str]:
    content = strip_code_fence(content)
    data: Any = json.loads(content)
    if isinstance(data, dict) and "translations" in data:
        arr = data["translations"]
    elif isinstance(data, list):
        arr = data
    else:
        raise ValueError("JSON 须为数组或包含 translations 数组的对象")
    if not isinstance(arr, list):
        raise ValueError("translations 必须是数组")
    if len(arr) != expected:
        raise ValueError(f"译文数量 {len(arr)} 与条目数 {expected} 不一致")
    out: list[str] = []
    for i, item in enumerate(arr):
        if not isinstance(item, str):
            raise ValueError(f"第 {i} 条译文不是字符串")
        out.append(item)
    return out


def deepseek_translate_batch(
    api_key: str,
    model: str,
    sources: list[str],
    lang: str,
    timeout: float,
) -> list[str]:
    hint = target_language_prompt(lang)
    # 紧凑 payload：同一批内多条只付一次 system + 短说明，减少重复 token
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Qt/PySide UI 翻译。保留占位符与格式：{var}、%1、%n、\\n 等，勿改占位符名。"
                    "仅输出 JSON 对象。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"目标：{hint}\n"
                    f'返回 {{"translations":["…"]}}，数组长度={len(sources)}，顺序与 sources 一致。\n'
                    f"sources={json.dumps(sources, ensure_ascii=False)}"
                ),
            },
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    r = requests.post(
        DEEPSEEK_API_URL,
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=timeout,
    )
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
    body = r.json()
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"响应结构异常: {body!r}") from e
    return parse_translations_json(content, len(sources))


def apply_translation(translation_el: ET.Element, text: str) -> None:
    translation_el.clear()
    translation_el.text = text
    if "type" in translation_el.attrib and translation_el.attrib.get("type") == "unfinished":
        del translation_el.attrib["type"]


def save_ts(tree: ET.ElementTree[Any], path: Path) -> None:
    root = tree.getroot()
    if root is None:
        raise RuntimeError("无效的 .ts XML：缺少根节点")
    ET.indent(root, space="    ")
    buf = io.StringIO()
    tree.write(buf, encoding="unicode", xml_declaration=False)
    body = buf.getvalue()
    out = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!DOCTYPE TS>\n"
        + body
        + ("\n" if not body.endswith("\n") else "")
    )
    path.write_text(out, encoding="utf-8")


def process_file(
    path: Path,
    api_key: str,
    model: str,
    filter_mode: str,
    skip_vanished: bool,
    batch_size: int,
    max_chars_per_batch: int,
    dry_run: bool,
    timeout: float,
    sleep_s: float,
    workers: int,
) -> tuple[int, int]:
    tree = ET.parse(path)
    root = tree.getroot()
    lang = root.get("language") or ""

    entries: list[tuple[ET.Element, str]] = []
    for ctx in root.findall("context"):
        for message in ctx.findall("message"):
            trans = message.find("translation")
            src_el = message.find("source")
            if trans is None or src_el is None:
                continue
            if not should_translate(trans, filter_mode, skip_vanished):
                continue
            src = element_plain_text(src_el)
            entries.append((trans, src))

    total = len(entries)
    if total == 0:
        print(f"{path}: 无待翻译条目（filter={filter_mode}）", file=sys.stderr)
        return 0, 0

    print(f"{path}: 待翻译 {total} 条（language={lang or '?'}）", file=sys.stderr)
    if dry_run:
        for _, s in entries[:10]:
            print(f"  - {s[:80]}{'…' if len(s) > 80 else ''}", file=sys.stderr)
        if total > 10:
            print(f"  ... 另有 {total - 10} 条", file=sys.stderr)
        batches = split_translation_entries_into_batches(
            entries, max_items=batch_size, max_chars=max_chars_per_batch
        )
        print(
            f"  dry-run：将分为 {len(batches)} 次 API 调用（batch≤{batch_size} 条"
            + (f"，≤{max_chars_per_batch} 字符/批" if max_chars_per_batch > 0 else "")
            + "）",
            file=sys.stderr,
        )
        return total, 0

    batches = split_translation_entries_into_batches(
        entries, max_items=batch_size, max_chars=max_chars_per_batch
    )
    nb = len(batches)
    print(
        f"  分 {nb} 批请求 API（每批最多 {batch_size} 条"
        + (f"，约 {max_chars_per_batch} 字符上限" if max_chars_per_batch > 0 else "")
        + "）",
        file=sys.stderr,
    )

    batch_trans_els: list[list[ET.Element]] = []
    batch_sources: list[list[str]] = []
    for batch in batches:
        batch_trans_els.append([t for t, _ in batch])
        batch_sources.append([s for _, s in batch])

    def translate_batch_index(batch_idx: int) -> tuple[int, list[str]]:
        trans_els = batch_trans_els[batch_idx]
        sources = batch_sources[batch_idx]
        outs = deepseek_translate_batch(api_key, model, sources, lang, timeout)
        if len(outs) != len(trans_els):
            raise RuntimeError("内部错误：译文与元素数量不一致")
        return batch_idx, outs

    progress_lock = threading.Lock()
    done_count = 0

    def on_progress(n: int) -> None:
        nonlocal done_count
        with progress_lock:
            done_count += n
            print(f"  已完成 {done_count}/{total}", file=sys.stderr)

    if workers <= 1:
        for batch_idx in range(nb):
            try:
                _, outs = translate_batch_index(batch_idx)
            except Exception as e:
                print(f"批次 {batch_idx + 1} 失败: {e}", file=sys.stderr)
                raise
            for el, text in zip(batch_trans_els[batch_idx], outs):
                apply_translation(el, text)
            on_progress(len(outs))
            if sleep_s > 0 and batch_idx < nb - 1:
                time.sleep(sleep_s)
    else:
        results: dict[int, list[str]] = {}
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {
                executor.submit(translate_batch_index, batch_idx): batch_idx
                for batch_idx in range(nb)
            }
            try:
                for fut in as_completed(future_map):
                    bidx = future_map[fut]
                    try:
                        bi, outs = fut.result()
                    except Exception as e:
                        print(f"批次 {bidx + 1} 失败: {e}", file=sys.stderr)
                        raise
                    results[bi] = outs
                    on_progress(len(outs))
            except Exception:
                for f in future_map:
                    f.cancel()
                raise
        for batch_idx in range(nb):
            outs = results[batch_idx]
            for el, text in zip(batch_trans_els[batch_idx], outs):
                apply_translation(el, text)

    save_ts(tree, path)
    return total, total


def main() -> None:
    root = repo_root()
    default_i18n = root / "app" / "i18n"

    p = argparse.ArgumentParser(description="使用 DeepSeek API 翻译 Qt .ts 文件")
    p.add_argument(
        "--files",
        nargs="*",
        type=Path,
        help=f".ts 路径，默认扫描 {default_i18n}",
    )
    p.add_argument(
        "--filter",
        choices=["unfinished", "empty", "both", "all"],
        default="both",
        help="unfinished: 仅 type=unfinished；empty: 仅空译文；both: 二者；all: 全部非 vanished",
    )
    p.add_argument(
        "--include-vanished",
        action="store_true",
        help="包含 type=vanished 的条目（默认跳过）",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        default=96,
        help="每批最多条数（与 --max-chars-per-batch 同时生效，先达到上限则切批）",
    )
    p.add_argument(
        "--max-chars-per-batch",
        type=int,
        default=48_000,
        help="每批 sources 总字符数上限（0=不按字符切分，仅按条数）。默认较大以合并更多短句，减少请求次数与重复 system prompt",
    )
    p.add_argument("--model", default=DEFAULT_MODEL, help="DeepSeek 模型名")
    p.add_argument(
        "--token-file",
        type=Path,
        default=None,
        help="覆盖默认的仓库根目录 .llm.txt",
    )
    p.add_argument(
        "--token-env",
        default="DEEPSEEK_API_KEY",
        help="若设置该环境变量则优先于 .llm.txt",
    )
    p.add_argument("--dry-run", action="store_true", help="只列出待翻译条目，不写文件、不调 API")
    p.add_argument("--timeout", type=float, default=120.0, help="单次请求超时（秒）")
    p.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="串行模式（--workers 1）下批次间隔休眠（秒）；并行时不生效",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=2,
        help="并行批次数（默认 2）。增大并行不省 token，仅加快；省 token 主要靠加大每批条数/字符上限",
    )
    args = p.parse_args()

    api_key = ""
    if not args.dry_run:
        env_key = args.token_env and os.environ.get(args.token_env)
        if env_key:
            api_key = env_key.strip()
        elif args.token_file:
            api_key = args.token_file.read_text(encoding="utf-8").strip()
            if not api_key:
                raise SystemExit("--token-file 为空")
        else:
            api_key = load_api_token(root)

    if args.files:
        files = [Path(f) for f in args.files]
    else:
        files = sorted(default_i18n.glob("*.ts"))
    files = [f if f.is_absolute() else root / f for f in files]
    for f in files:
        if not f.is_file():
            raise SystemExit(f"文件不存在: {f}")

    skip_vanished = not args.include_vanished
    grand_total = 0
    grand_done = 0
    for f in files:
        t, d = process_file(
            f,
            api_key=api_key,
            model=args.model,
            filter_mode=args.filter,
            skip_vanished=skip_vanished,
            batch_size=max(1, args.batch_size),
            max_chars_per_batch=max(0, args.max_chars_per_batch),
            dry_run=args.dry_run,
            timeout=args.timeout,
            sleep_s=max(0.0, args.sleep),
            workers=max(1, args.workers),
        )
        grand_total += t
        grand_done += d

    if args.dry_run:
        print(f"dry-run：共 {grand_total} 条待处理", file=sys.stderr)
    else:
        print(f"完成：共写入 {grand_done} 条译文", file=sys.stderr)


if __name__ == "__main__":
    main()
