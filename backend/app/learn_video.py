"""课程讲解视频脚本编译器。

把每节课**已经写好的**字段（definition / plain / example / pitfalls / task）
编译成前端播放器能直接播的分镜脚本。三条硬规则：

1. **不虚构内容**。画面文字和旁白全部来自课程原文，只做「去 Markdown、
   分句、截断」，不额外编造知识点。课程文案改了，视频跟着改。
2. **代码分镜真执行**。「这一行跑完变量变成什么」是把 `example` 真的跑一遍、
   用 `sys.settrace` 抓下来的快照，不是猜的 —— 猜错会直接教错学生。
3. **构建期生成**。113 课全部编译一次落到 `lesson_videos.json`，
   运行时只读 JSON，不给接口加毫秒级开销（跑一遍 113 个 example 要好几秒）。

分镜固定五段，对应 `scenes[].kind`：

    title   标题卡
    lines   逐句浮现的要点（来自 plain）
    code    python：逐行高亮 + 变量表 + 输出
    commands sql / Redis 这类：命令逐行显现 + 结果块
    pitfalls 易错点
    task    动手任务
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------- 文本处理 ----------

_CODE_FENCE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.S)
_INLINE_CODE = re.compile(r"`([^`]*)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_LIST_MARK = re.compile(r"^\s*(?:[-+*]|\d+\.)\s+", re.M)
_HEADING = re.compile(r"^\s*#{1,6}\s*", re.M)
_SENT_SPLIT = re.compile(r"(?<=[。！？!?；;])")


def strip_md(text: str) -> str:
    """去掉 Markdown 标记，留给「念出来」和「大字展示」。"""
    if not text:
        return ""
    text = _CODE_FENCE.sub(lambda m: m.group(1), text)
    text = _INLINE_CODE.sub(r"\1", text)
    text = _BOLD.sub(r"\1", text)
    text = _ITALIC.sub(r"\1", text)
    text = _HEADING.sub("", text)
    text = _LIST_MARK.sub("", text)
    return text.strip()


def sentences(text: str) -> list[str]:
    """按中文标点切句，去掉空句。"""
    plain = strip_md(text).replace("\n", " ")
    return [s.strip() for s in _SENT_SPLIT.split(plain) if s.strip()]


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _speech(text: str, limit: int = 120) -> str:
    """配音稿：去掉不利于朗读的符号，截断到一句左右。"""
    text = strip_md(text)
    text = re.sub(r"[`*#>|]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = _clip(text, limit)
    if text and text[-1] in "；;，,":
        text = text[:-1] + "。"
    elif text and text[-1] not in "。！？!?…":
        text += "。"
    return text


# ---------- 代码分镜：真执行 + 逐行快照 ----------

_HARNESS = r'''
import io, json, sys

code = sys.stdin.read()
buf = io.StringIO()
orig = sys.stdout
steps = []
MAX_STEPS = 400


def _ser(v):
    t = type(v).__name__
    if t not in ("int", "float", "bool", "str", "NoneType", "list", "dict", "tuple", "set"):
        return None
    try:
        s = repr(v)
    except Exception:
        return None
    if len(s) > 64:
        return None
    return s


def _tracer(frame, event, arg):
    if event != "line" or frame.f_code.co_filename != "<lesson>":
        return _tracer
    if len(steps) >= MAX_STEPS:
        return _tracer
    snap = {}
    for k, v in frame.f_locals.items():
        if k.startswith("_") or k == "__builtins__":
            continue
        sv = _ser(v)
        if sv is not None:
            snap[k] = sv
    steps.append({"line": frame.f_lineno - 1, "vars": snap, "at": len(buf.getvalue())})
    return _tracer


glob = {"__name__": "__main__"}
sys.stdout = buf
try:
    sys.settrace(_tracer)
    exec(compile(code, "<lesson>", "exec"), glob)
finally:
    sys.settrace(None)
    sys.stdout = orig

full = buf.getvalue()
for i, s in enumerate(steps):
    end = steps[i + 1]["at"] if i + 1 < len(steps) else len(full)
    s["out"] = full[s["at"]:end]
    del s["at"]
final = {}
for k, v in glob.items():
    if k.startswith("_") or k == "__builtins__":
        continue
    sv = _ser(v)
    if sv is not None:
        final[k] = sv
sys.__stdout__.write(json.dumps(
    {"steps": steps, "output": full, "final": final}, ensure_ascii=False))
'''


def trace_python(code: str, timeout: int = 25) -> dict:
    """在子进程里跑一遍示例代码，返回逐行变量快照。

    用子进程而不是在本进程 settrace：示例里可能有 numpy/pandas 导入、
    甚至死循环，隔离掉才不会把构建脚本一起拖死。
    """
    try:
        with tempfile.TemporaryDirectory() as tmp:
            harness = Path(tmp) / "harness.py"
            harness.write_text(_HARNESS, encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-u", str(harness)],
                input=code,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
                creationflags=0x08000000 if sys.platform == "win32" else 0,
            )
        if proc.returncode != 0 or not proc.stdout.strip():
            return {"steps": [], "output": "", "final": {},
                    "error": (proc.stderr or "")[:200]}
        data = json.loads(proc.stdout)
        return {"steps": data.get("steps", []),
                "output": data.get("output", ""),
                "final": data.get("final", {}), "error": ""}
    except subprocess.TimeoutExpired:
        return {"steps": [], "output": "", "final": {}, "error": "示例运行超时"}
    except Exception as exc:  # noqa: BLE001 - 构建期出错就降级，不影响其它课
        return {"steps": [], "output": "", "final": {}, "error": str(exc)[:200]}


MAX_CODE_LINES = 22


def _code_lines(code: str) -> list[str]:
    lines = code.replace("\r\n", "\n").split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    if len(lines) > MAX_CODE_LINES:
        lines = lines[:MAX_CODE_LINES] + ["# ……（示例较长，这里只演示前 22 行）"]
    return lines


def _merge_steps(rawn: list[dict], final: dict | None = None) -> list[dict]:
    """整理逐行快照。

    两个要点：
    - 同一行被执行多次（循环）时只保留最后一次，避免高亮来回跳；
    - settrace 是在**行执行前**触发的，所以本行的「执行后状态」要取
      **下一条快照**的 vars。否则学生会看到 `age = age + 1` 执行完 age 还是旧值，
      那是明确的错误教学。
    """
    if not rawn:
        return []
    last_idx: dict[int, int] = {}
    order: list[int] = []
    for i, s in enumerate(rawn):
        ln = int(s.get("line", 0))
        if ln not in last_idx:
            order.append(ln)
        last_idx[ln] = i
    out: list[dict] = []
    for ln in order:
        i = last_idx[ln]
        after = rawn[i + 1]["vars"] if i + 1 < len(rawn) else (final or {})
        outs = "".join(s.get("out", "") for s in rawn if int(s.get("line", 0)) == ln)
        out.append({"line": ln, "vars": after, "out": outs})
    return out


# ---------- 分镜构建 ----------

def _scene_title(p: dict) -> dict:
    say = f"{p['subject']}，第 {p['order_no']} 课：{p['title']}。{_speech(p.get('summary', ''), 60)}"
    return {
        "kind": "title",
        "dur": 4600,
        "eyebrow": f"{p['subject']} · 第 {p['order_no']} 课",
        "title": p["title"],
        "sub": strip_md(p.get("summary", "")),
        "say": say,
    }


def _scene_lines(p: dict) -> dict:
    """把 plain 拆成 2~3 条「大字要点」逐句浮现。

    优先取带比喻意味的前几句 —— plain 本来就是全课最口语化的一段。
    """
    sents = sentences(p.get("plain", ""))
    if not sents:
        sents = sentences(p.get("definition", ""))
    items = [ _clip(s, 92) for s in sents[:3] ] or ["这一课没有额外的通俗解释。"]
    say = _speech("".join(sents[:2]), 150)
    return {
        "kind": "lines",
        "dur": 3200 + 2100 * len(items),
        "heading": "一句话讲透",
        "items": items,
        "say": say,
    }


def _scene_code(p: dict) -> dict | None:
    """python 课：真跑一遍，逐行快照。跑不通就只展示静态代码。"""
    code = (p.get("example") or "").strip()
    if not code or "```" in code:
        return None
    lines = _code_lines(code)
    traced = trace_python(code)
    steps = _merge_steps(traced["steps"], traced.get("final"))
    steps = [s for s in steps if s["line"] < len(lines)]
    output = traced["output"].strip("\n")
    if not output:
        output = (p.get("example_output") or "").strip("\n")
    say = "看一个例子，注意右边变量的变化。"
    if traced["error"]:
        say = "看一个例子。"
    return {
        "kind": "code",
        "dur": 3400 + 1600 * max(1, len(steps)),
        "lang": "python",
        "caption": "示例代码",
        "lines": lines,
        "steps": steps,
        "output": output,
        "say": say,
    }


def _scene_commands(p: dict) -> dict:
    """sql / Redis 这类：命令逐行显现，结果单独成块。"""
    raw = (p.get("example") or "").strip("\n")
    lines = [ln.rstrip() for ln in raw.replace("\r\n", "\n").split("\n")]
    lines = [ln for ln in lines if ln.strip()][:MAX_CODE_LINES]
    kind = "sql" if p.get("runner") == "sql" else "shell"
    output = (p.get("example_output") or "").strip("\n")
    return {
        "kind": "commands",
        "dur": 3000 + 1400 * len(lines),
        "lang": kind,
        "caption": "示例命令" if kind == "shell" else "示例 SQL",
        "lines": lines,
        "output": output,
        "say": "看一个例子。",
    }


def _scene_pitfalls(p: dict) -> dict | None:
    items = [ _clip(strip_md(x), 74) for x in (p.get("pitfalls") or []) ]
    items = [x for x in items if x]
    if not items:
        return None
    items = items[:4]
    say = "这里有几个容易踩的坑。"
    if items:
        say += _speech(p["pitfalls"][0], 90)
    return {
        "kind": "pitfalls",
        "dur": 2800 + 1900 * len(items),
        "heading": f"{len(items)} 个容易踩的坑",
        "items": items,
        "say": say,
    }


def _scene_task(p: dict) -> dict | None:
    task = (p.get("task") or "").strip()
    if not task:
        return None
    sents = sentences(task)
    head = _clip(strip_md(" ".join(sents[:2])), 110)
    bullets = [ _clip(strip_md(s), 64) for s in sents[1:5] ]
    bullets = [b for b in bullets if b]
    say = "轮到你动手了，照着任务要求写一写。"
    return {
        "kind": "task",
        "dur": 4200 + 700 * len(bullets),
        "heading": "轮到你了",
        "text": head,
        "bullets": bullets[:3],
        "say": say,
    }


def build_video(p: dict) -> dict:
    """把一节课编译成完整分镜脚本。"""
    runner = p.get("runner", "python")
    scenes: list[dict] = [_scene_title(p), _scene_lines(p)]
    code_scene = _scene_code(p) if runner == "python" else _scene_commands(p)
    if code_scene:
        scenes.append(code_scene)
    for fn in (_scene_pitfalls, _scene_task):
        s = fn(p)
        if s:
            scenes.append(s)
    return {
        "code": p["code"],
        "scenes": scenes,
        "duration_ms": sum(s["dur"] for s in scenes),
    }


def build_all(points: list[dict]) -> dict:
    videos = {}
    for p in points:
        try:
            videos[p["code"]] = build_video(p)
        except Exception as exc:  # noqa: BLE001
            videos[p["code"]] = {"code": p["code"], "scenes": [], "duration_ms": 0,
                                 "error": str(exc)[:160]}
    return videos


def load_videos() -> dict:
    """读构建期生成的 JSON；缺失时返回空字典（接口那边会退化成不显示视频）。"""
    path = Path(__file__).with_name("seed") / "lesson_videos.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
