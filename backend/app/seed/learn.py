"""引导式课程总入口。

内容按科目拆在多个文件里，这里统一汇总：

- Python 四阶段     → learn_basics / learn_advanced / learn_agent
- MySQL             → learn_db
- Redis             → learn_redis
- 计算机网络        → learn_net
- 数据结构          → learn_ds
- 操作系统          → learn_os
- 数据分析与处理    → learn_data
- Transformer       → learn_tf

每个知识点自带 `subject`（科目）与 `stage`（科目内的分组）。
`order_no` 是**科目内**序号，从 1 开始 —— 因为解锁是按科目独立走的，
跨科目连号没有意义（不该出现"MySQL 第 35 课"这种编号）。

解锁顺序 = 科目内的课程顺序：本课判定通过，**同科目**的下一课才解锁；
每个科目的第一课默认就是解锁的，科目之间互不阻塞。
"""

from .learn_advanced import LESSONS as ADVANCED
from .learn_agent import LESSONS as AGENT
from .learn_basics import LESSONS as BASICS
from .learn_data import LESSONS as DATA
from .learn_db import LESSONS as DB
from .learn_ds import LESSONS as DS
from .learn_net import LESSONS as NET
from .learn_os import LESSONS as OS
from .learn_redis import LESSONS as REDIS
from .learn_tf import LESSONS as TF

# Python 是最早的一批课程，dict 里没有 subject/runner 字段。
# 这里统一补齐，免得去改 34 个知识点。
_PYTHON: list[dict] = BASICS + ADVANCED + AGENT
for _p in _PYTHON:
    _p.setdefault("subject", "Python")
    _p.setdefault("runner", "python")

# 科目顺序 = 前端 Tab 的顺序
TRACKS: list[tuple[str, list[dict]]] = [
    ("Python", _PYTHON),
    ("MySQL", DB),
    ("Redis", REDIS),
    ("计算机网络", NET),
    ("数据结构", DS),
    ("操作系统", OS),
    ("数据分析与处理", DATA),
    ("Transformer", TF),
]

SUBJECTS: list[str] = [name for name, _ in TRACKS]

# 科目 → 该科目的知识点，order_no 在科目内重新编号
BY_SUBJECT: dict[str, list[dict]] = {
    name: [{**p, "order_no": i + 1} for i, p in enumerate(lessons)]
    for name, lessons in TRACKS
}

CURRICULUM: list[dict] = [p for name in SUBJECTS for p in BY_SUBJECT[name]]

BY_CODE: dict[str, dict] = {p["code"]: p for p in CURRICULUM}

# 科目 → 科目内的分组顺序（前端分组展示用）
STAGES_BY_SUBJECT: dict[str, list[str]] = {
    name: list(dict.fromkeys(p["stage"] for p in BY_SUBJECT[name]))
    for name in SUBJECTS
}


def next_code(code: str) -> str | None:
    """同科目里的下一个知识点；已经是本科目最后一课就返回 None。"""
    point = BY_CODE.get(code)
    if not point:
        return None
    codes = [p["code"] for p in BY_SUBJECT[point["subject"]]]
    i = codes.index(code)
    return codes[i + 1] if i + 1 < len(codes) else None
