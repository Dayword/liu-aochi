"""代码运行沙箱（本地演示版，仅 Python）。

安全限制：超时、体积限制、危险模块黑名单。
生产环境应按设计文档替换为 Judge0/Docker 隔离沙箱。
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

from ..config import settings

# 危险模块黑名单（演示环境防误操作；无法阻止所有逃逸，切勿用于生产）
BLOCKED_MODULES = {
    "os", "subprocess", "socket", "ctypes", "shutil", "pathlib",
    "importlib", "multiprocessing", "pickle", "marshal", "inspect",
    "pdb", "tkinter", "webbrowser", "pty", "fcntl", "winreg",
}
BLOCK_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+(" + "|".join(sorted(BLOCKED_MODULES)) + r")(?:\.|\s|$)",
    re.MULTILINE | re.IGNORECASE,
)


def check_code_safety(code: str) -> str | None:
    """返回违规说明或 None。"""
    if len(code.encode("utf-8")) > settings.CODE_MAX_SIZE:
        return "代码超过体积限制"
    for m in BLOCK_PATTERN.finditer(code):
        return f"出于演示环境安全考虑，禁止导入模块：{m.group(1)}"
    if "__import__" in code or "eval(" in code or "exec(" in code:
        return "出于演示环境安全考虑，禁止动态执行（__import__/eval/exec）"
    return None


def run_python(code: str, stdin_data: str = "") -> dict:
    """执行 Python 代码，返回输出/错误/耗时。"""
    err = check_code_safety(code)
    if err:
        return {"stdout": "", "stderr": err, "exit_code": 1, "time_ms": 0}
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-u", "-c", code],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=settings.CODE_RUN_TIMEOUT,
            creationflags=0x08000000 if sys.platform == "win32" else 0,  # CREATE_NO_WINDOW
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
            "time_ms": int((time.time() - start) * 1000),
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"运行超时（>{settings.CODE_RUN_TIMEOUT}s）",
                "exit_code": 124, "time_ms": int((time.time() - start) * 1000)}


def run_with_tests(code: str, test_cases: list[dict]) -> tuple[list[dict], int, int]:
    """按测试用例运行：test_cases=[{input, expected}]，input 为 stdin 文本。"""
    results: list[dict] = []
    passed = 0
    for tc in test_cases:
        inp = tc.get("input", "")
        expected = str(tc.get("expected", "")).strip()
        r = run_python(code, inp)
        got = r["stdout"].strip()
        ok = (r["exit_code"] == 0) and (got == expected)
        if ok:
            passed += 1
        results.append({"input": inp[:80], "expected": expected[:120],
                        "got": got[:120], "passed": ok,
                        "time_ms": r.get("time_ms", 0),
                        "stderr": r["stderr"][:200]})
    return results, passed, len(test_cases)


def judge_bug_fix(fixed_code: str, test_cases: list[dict]) -> dict:
    """Bug 猎人判定：正确率 + 耗时 + 简单质量分。"""
    if not fixed_code.strip():
        return {"results": [], "passed": 0, "total": 0, "accuracy": 0.0,
                "speed_ms": 0, "quality": 0.0, "err": "提交内容为空"}
    err = check_code_safety(fixed_code)
    if err:
        return {"results": [], "passed": 0, "total": 0, "accuracy": 0.0,
                "speed_ms": 0, "quality": 0.0, "err": err}
    results, passed, total = run_with_tests(fixed_code, test_cases)
    accuracy = round(passed / total * 100, 1) if total else 0.0
    speeds = [r["time_ms"] for r in results if r["passed"]]
    speed_ms = int(sum(speeds) / len(speeds)) if speeds else 0
    # 简单质量启发：行数、注释、命名规范
    lines = [l for l in fixed_code.splitlines() if l.strip()]
    quality = 50.0
    if 2 <= len(lines) <= 40:
        quality += 20
    if "def " in fixed_code and "return" in fixed_code:
        quality += 15
    if fixed_code.count("#") >= 1:
        quality += 10
    quality = round(min(100, quality), 1)
    return {"results": results, "passed": passed, "total": total,
            "accuracy": accuracy, "speed_ms": speed_ms, "quality": quality, "err": ""}
