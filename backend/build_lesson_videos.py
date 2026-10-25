"""构建期脚本：把当前全部课程（CURRICULUM）编译成讲解视频脚本。

    cd backend && python build_lesson_videos.py          # 生成
    cd backend && python build_lesson_videos.py --check  # 只看差异，不写文件

产物：backend/app/seed/lesson_videos.json

为什么不放在接口里实时算：python 课的「逐行变量快照」要把 example 真跑一遍，
70 个示例累计要一分多钟。丢给构建期，运行时只读 JSON。

**改过任何课程文案（definition/plain/example/pitfalls/task）之后都要重跑本脚本**，
否则视频里还是旧内容 —— 这一点和 seed 改动必须重启后端是同一类坑。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from app.learn_video import build_video
from app.seed.learn import CURRICULUM

OUT = Path(__file__).parent / "app" / "seed" / "lesson_videos.json"


def main() -> int:
    check_only = "--check" in sys.argv
    started = time.time()
    videos: dict[str, dict] = {}
    failures: list[tuple[str, str]] = []
    empty: list[str] = []

    for i, p in enumerate(CURRICULUM, 1):
        code = p["code"]
        try:
            v = build_video(p)
        except Exception as exc:  # noqa: BLE001
            failures.append((code, str(exc)[:100]))
            continue
        if not v["scenes"]:
            empty.append(code)
        videos[code] = v
        print(f"\r[{i:3d}/{len(CURRICULUM)}] {code:<18}", end="", flush=True)

    print()
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            old = {}

    changed = [c for c in videos if old.get(c) != videos[c]]
    total_ms = sum(v["duration_ms"] for v in videos.values())
    with_code = sum(1 for v in videos.values() if any(s["kind"] == "code" for s in v["scenes"]))
    with_cmd = sum(1 for v in videos.values() if any(s["kind"] == "commands" for s in v["scenes"]))

    print(f"课数        {len(videos)}/{len(CURRICULUM)}")
    print(f"总时长      {total_ms / 1000:.0f} 秒（平均 {total_ms / max(1, len(videos)) / 1000:.1f} 秒/课）")
    print(f"代码分镜    {with_code} 课（含逐行变量快照）")
    print(f"命令分镜    {with_cmd} 课（SQL / Redis 等）")
    print(f"编译失败    {len(failures)}")
    for c, e in failures:
        print(f"  ! {c}: {e}")
    if empty:
        print(f"空分镜      {len(empty)}: {empty[:8]}")
    if old:
        print(f"内容有变化  {len(changed)} 课")

    if check_only:
        return 1 if failures else 0

    OUT.write_text(json.dumps(videos, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"已写入      {OUT.relative_to(Path(__file__).parent)} "
          f"（{OUT.stat().st_size / 1024:.0f} KB，耗时 {time.time() - started:.1f}s）")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
