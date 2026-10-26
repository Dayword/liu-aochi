"""代码运行沙箱（公网可用版，仅 Python）。

相比初版「危险模块黑名单」，这里改成四层防护：

1. **AST 白名单**：解析语法树，逐个检查 `import` / `from ... import` 的顶级模块名，
   只放行教学需要的库。基于正则的黑名单很容易用 `import o''s`、动态导入绕过，
   AST 只看真实语义，绕过成本高得多。
2. **高危名字拦截**：`__import__` / `eval` / `exec` / `compile` / `__builtins__`
   以及 `__subclasses__` / `__globals__` / `__bases__` 等属性链逃逸入口。
3. **进程级隔离**（Linux）：`unshare -n` 断网；`setrlimit` 限内存 / CPU / 文件大小；
   `start_new_session` 便于超时时杀掉整棵进程树；cwd 指向一次性临时目录；
   环境变量最小化（**绝不把 .env 里的 AI Key 传给子进程**）。
4. **输出截断**：`print` 炸弹不会撑爆响应体和内存。

⚠️ 残余风险：文本层仍无法 100% 阻止逃逸（例如通过 `getattr` 拼字符串访问危险属性）。
因此本沙箱定位是「教学演示 + 提高攻击成本」，不是安全边界。公网长期运行请在
`.env` 里设 `CODE_RUN_ENABLED=false` 关闭，或按设计文档换成 Judge0 / Docker 隔离。
"""
from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from functools import lru_cache
from pathlib import Path

from ..config import settings

# ---------- 第一层：模块白名单 ----------
# 只放教学确实会用到的库。加新库前先想清楚：这个库能不能读文件、发网络请求、起进程？
ALLOWED_MODULES = {
    # 标准库（纯计算 / 文本 / 时间 / 数据结构）
    "math", "cmath", "random", "statistics", "decimal", "fractions", "numbers",
    "re", "json", "string", "textwrap", "unicodedata", "collections", "itertools",
    "functools", "operator", "heapq", "bisect", "copy", "enum", "dataclasses",
    "abc", "typing", "pprint", "datetime", "calendar", "zoneinfo", "time",
    "hashlib", "hmac", "base64", "uuid", "array", "queue", "threading",
    "concurrent", "asyncio", "contextlib", "warnings",
    # 数据分析（课程「数据分析与处理」科目要用）
    "numpy", "pandas",
    # 数据校验（课程「AI 工程质量」用 pydantic 讲结构化输出校验）
    "pydantic",
}

# 明确拒绝时给出的提示（比“禁止导入”更友好，也告诉学生该换什么）
_DENIED_HINTS = {
    "os": "沙箱不提供文件系统与进程能力",
    "sys": "沙箱不提供解释器内部信息",
    "subprocess": "沙箱不允许启动新进程",
    "socket": "沙箱不提供网络能力",
    "urllib": "沙箱不提供网络能力",
    "http": "沙箱不提供网络能力",
    "requests": "沙箱不提供网络能力",
    "shutil": "沙箱不提供文件系统能力",
    "pathlib": "沙箱不提供文件系统能力",
    "tempfile": "沙箱不提供文件系统能力",
    "importlib": "沙箱不允许动态导入",
    "ctypes": "沙箱不允许调用原生代码",
    "pickle": "沙箱不允许反序列化",
    "multiprocessing": "沙箱不允许创建子进程",
}

# ---------- 第二层：高危名字 ----------
FORBIDDEN_NAMES = {
    "__import__", "eval", "exec", "compile", "breakpoint",
    "__builtins__", "__loader__", "__spec__", "__subclasses__",
    "__globals__", "__bases__", "__mro__", "__code__", "__getattribute__",
    "__reduce__", "__reduce_ex__", "__setstate__",
}


def _check_ast(code: str) -> str | None:
    """AST 层检查。语法错误的代码交给解释器自己报错（它也跑不起来，无风险）。"""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return None

    for node in ast.walk(tree):
        # import xxx / from xxx import yyy
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_MODULES:
                    hint = _DENIED_HINTS.get(root, "它不在沙箱允许的模块列表内")
                    return f"沙箱暂不支持导入模块「{root}」：{hint}"
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level:  # 相对导入
                return "沙箱不支持相对导入"
            if root and root not in ALLOWED_MODULES:
                hint = _DENIED_HINTS.get(root, "它不在沙箱允许的模块列表内")
                return f"沙箱暂不支持导入模块「{root}」：{hint}"
        # 名字：拦住 __builtins__ / __import__ / eval 等
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return f"出于安全考虑，禁止使用 {node.id}"
        # 属性：拦住 obj.__globals__ / __subclasses__ 这类逃逸链
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_NAMES:
            return f"出于安全考虑，禁止访问属性 {node.attr}"
    return None


def check_code_safety(code: str) -> str | None:
    """返回违规说明或 None。"""
    if len(code.encode("utf-8")) > settings.CODE_MAX_SIZE:
        return f"代码超过体积限制（{settings.CODE_MAX_SIZE // 1024} KB）"
    return _check_ast(code)


# ---------- 第三层：进程隔离 ----------
@lru_cache(maxsize=1)
def _network_isolation_prefix() -> list[str]:
    """探测能否用 `unshare -n` 断网。探测失败就退化，绝不能让学生代码因此报错。"""
    if not sys.platform.startswith("linux"):
        return []
    exe = shutil.which("unshare")
    if not exe:
        return []
    try:
        probe = subprocess.run([exe, "-n", "-r", "python3", "-c", "print(1)"],
                               capture_output=True, timeout=5)
        if probe.returncode == 0:
            return [exe, "-n", "-r", "--"]
    except Exception:
        pass
    return []


def _apply_limits(limit_seconds: int):
    """返回 preexec_fn：限制内存 / CPU / 单文件大小。仅 POSIX 有效。"""
    if os.name != "posix":
        return None

    def _set():
        try:
            import resource
            mem = settings.CODE_MAX_MEMORY_MB * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
            resource.setrlimit(resource.RLIMIT_CPU, (limit_seconds + 1, limit_seconds + 2))
            fsize = settings.CODE_MAX_FILE_BYTES
            resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))
            resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        except Exception:
            pass

    return _set


def _child_env(workdir: str) -> dict[str, str]:
    """最小化环境变量：**不继承 AI Key / 数据库密码**。

    ⚠️ Windows 上不能什么都不给：缺 `SystemRoot` 会导致 winsock 初始化失败
    （asyncio 的 `_overlapped` 直接报 WinError 10106）。所以这里按白名单
    保留系统必需的路径类变量 —— 它们不含任何密钥。
    """
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "HOME": workdir,
        "TMPDIR": workdir,
        "TEMP": workdir,
        "TMP": workdir,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "MPLBACKEND": "Agg",
    }
    for key in ("SystemRoot", "SystemDrive", "windir", "COMSPEC", "PATHEXT",
                "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS", "OS"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    return env


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…（输出过长，已截断到 {limit} 字符）"


# 全局并发名额：自由运行、课程判定、离线自检都走同一个池子，防止叠加超卖。
_slots = threading.BoundedSemaphore(max(1, settings.CODE_MAX_CONCURRENCY))
# 排队多久还没轮到就放弃。故意设短：学生宁可立刻看到「稍后再试」，
# 也不愿意盯着转圈十几秒。
_SLOT_WAIT_SECONDS = 2.0


def run_python(code: str, stdin_data: str = "", timeout: int | None = None,
               strict: bool = True) -> dict:
    """执行 Python 代码，返回输出/错误/耗时。

    `timeout` 不传就用配置里的 CODE_RUN_TIMEOUT（学生提交走这条路）；
    离线自检脚本可以传一个更宽松的值 —— 像 numpy / pandas 首次导入本身就要一秒多，
    不该因为机器忙就被判成「跑不通」。

    `strict=False` 仅供本地自检脚本使用，跳过文件大小等运行时限制，行为与生产一致即可。
    """
    err = check_code_safety(code)
    if err:
        return {"stdout": "", "stderr": err, "exit_code": 1, "time_ms": 0}

    # 并发闸门：2C2G 上同时起太多子进程会撞 OOM，内核通常先杀 MySQL。
    # 拿不到名额时**快速失败**而不是长时间阻塞 —— 同步路由跑在 FastAPI 的
    # 线程池里，几十个请求同时干等会把线程占满，连不跑代码的接口一起拖死。
    if not _slots.acquire(timeout=_SLOT_WAIT_SECONDS):
        return {
            "stdout": "",
            "stderr": "当前同时运行代码的人有点多，请等几秒再点一次「运行」",
            "exit_code": 125,
            "time_ms": 0,
        }
    try:
        return _execute_locked(code, stdin_data, timeout)
    finally:
        _slots.release()


def _execute_locked(code: str, stdin_data: str, timeout: int | None) -> dict:
    """真正起子进程执行；调用方必须已持有 _slots 名额。"""
    limit = timeout or settings.CODE_RUN_TIMEOUT
    start = time.time()
    workdir = tempfile.mkdtemp(prefix="ca_sandbox_")
    # `-X utf8` 强制子进程用 UTF-8 做标准 I/O：Windows 控制台默认 GBK，
    # 不强制的话中文输出会和我们这边的 utf-8 解码打架，变成满屏乱码。
    cmd = _network_isolation_prefix() + [
        sys.executable, "-X", "utf8", "-I", "-B", "-u", "-c", code]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=workdir,
            env=_child_env(workdir),
            preexec_fn=_apply_limits(limit),
            start_new_session=(os.name == "posix"),
            creationflags=0x08000000 if sys.platform == "win32" else 0,  # CREATE_NO_WINDOW
        )
        try:
            out, errout = proc.communicate(input=stdin_data or "", timeout=limit)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            out, errout = proc.communicate()
            return {
                "stdout": _truncate(out or "", settings.CODE_MAX_OUTPUT),
                "stderr": f"运行超时（>{limit}s）：请检查是否存在死循环，或输入数据过大",
                "exit_code": 124,
                "time_ms": int((time.time() - start) * 1000),
            }
        return {
            "stdout": _truncate(out or "", settings.CODE_MAX_OUTPUT),
            "stderr": _truncate(errout or "", settings.CODE_MAX_OUTPUT),
            "exit_code": proc.returncode,
            "time_ms": int((time.time() - start) * 1000),
        }
    except FileNotFoundError:
        return {"stdout": "", "stderr": "服务器未安装可用的 Python 解释器",
                "exit_code": 127, "time_ms": 0}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _kill_tree(proc: subprocess.Popen) -> None:
    """杀掉整个进程会话，避免学生代码留下的子进程占用 CPU。"""
    try:
        if os.name == "posix":
            import signal
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        else:
            proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


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
