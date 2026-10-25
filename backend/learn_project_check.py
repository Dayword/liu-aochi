"""核验「项目实地」里每一处引用的文件与行号是否还对得上。

背景：113 课里 76 条 `kind=used` 都写了 `文件:行号` 和一段真实代码摘录。
一旦鸭先知项目（D:/PythonProject/游乐场智能rag问答系统）继续改动，
行号会漂移，学生按行号去对照就找不到东西 —— 这种「看起来有据可查、实际对不上」
比不写还糟。所以把核验固化成脚本，改完项目代码跑一次即可。

用法（backend 目录下）：
    python learn_project_check.py            # 只核验
    python learn_project_check.py --verbose  # 打印每一条的命中行

规则：`used` 条目里所有「像代码」的行（去空白后长度 >= 14，且不是省略号），
都必须在 `文件:行号` 声明的区间内（前后各留 1 行容差）找得到。
`absent` 条目没有行号要求，只检查 file 指向的文件是否存在（为空则跳过）。

退出码：0 全部通过 / 1 有对不上的 / 2 项目目录不存在（不是错误，是跳过）
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from app.seed.learn_project import REFS
from app.seed.learn_project_base import PROJECT_PATH

TOLERANCE = 1


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _parse_range(raw: str) -> tuple[int, int] | None:
    m = re.match(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s*$", raw or "")
    if not m:
        return None
    start = int(m.group(1))
    return start, int(m.group(2) or start)


def _iter(verbose: bool) -> int:
    root = Path(PROJECT_PATH)
    if not root.is_dir():
        print(f"[跳过] 找不到项目目录：{root}")
        print("       这个脚本依赖本地那份鸭先知项目，换机器跑就会跳过，不算失败。")
        return 0

    used = [c for c, r in REFS.items() if r["kind"] == "used"]
    problems: list[str] = []
    checks = 0

    for code, ref in REFS.items():
        path = root / ref["file"].replace("/", os.sep) if ref["file"] else None
        if path is None:
            continue
        if not path.is_file():
            problems.append(f"{code}: 文件不存在 -> {ref['file']}")
            continue
        if ref["kind"] == "absent":
            continue

        rng = _parse_range(ref["lines"])
        if rng is None:
            problems.append(f"{code}: 行号格式不对 -> {ref['lines']!r}")
            continue
        start, end = rng

        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        anchors = [
            ln for ln in ref["snippet"].splitlines()
            if len(_norm(ln)) >= 14 and _norm(ln) not in ("...", "…")
        ]
        if not anchors:
            problems.append(f"{code}: 代码摘录太短，无法核验")
            continue

        for anchor in anchors:
            checks += 1
            needle = _norm(anchor)[:26]
            hits = [i for i, ln in enumerate(lines, 1) if needle in _norm(ln)]
            ok = any(start - TOLERANCE <= h <= end + TOLERANCE for h in hits)
            if not ok:
                where = ("实际在 %s 行" % hits[:3]) if hits else "文件里找不到这一行"
                problems.append(
                    f"{code}: {ref['file']}:{ref['lines']} 对不上 -> {anchor.strip()[:50]!r}（{where}）"
                )
            elif verbose:
                print(f"  ok  {code:<14} {ref['file']}:{ref['lines']}")

    print()
    print(f"used 条目：{len(used)}    代码行核验：{checks} 条    问题：{len(problems)}")
    if problems:
        print()
        for p in problems:
            print("  ✗", p)
        return 1
    print("全部通过：每一处引用的行号都能对上源文件。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="核验项目实地引用的文件与行号")
    ap.add_argument("--verbose", action="store_true", help="打印每一条的核验结果")
    args = ap.parse_args()
    return _iter(args.verbose)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    raise SystemExit(main())
