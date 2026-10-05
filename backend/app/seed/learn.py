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
from .learn_ai_adv import LESSONS as AI_ADV
from .learn_basics import LESSONS as BASICS
from .learn_data import LESSONS as DATA
from .learn_db import LESSONS as DB
from .learn_ds import LESSONS as DS
from .learn_eng_adv import LESSONS as ENG_ADV
from .learn_net import LESSONS as NET
from .learn_os import LESSONS as OS
from .learn_py_core import LESSONS as PY_CORE
from .learn_py_extra import LESSONS as PY_EXTRA
from .learn_py_oop import LESSONS as PY_OOP
from .learn_redis import LESSONS as REDIS
from .learn_tf import LESSONS as TF

# Python 是最早的一批课程，dict 里没有 subject/runner 字段。
# 这里统一补齐，免得去改每一个知识点。
#
# 顺序 = 学习链顺序：
#   基础 → 基础补强 → 进阶 → 面向对象 → 进阶补强
#   → 工程基础 → AI Agent 开发 → 工程进阶 → AI Agent 进阶
#
# ⚠️ 后加的「补充课」都带 supplementary=True，它们**不参与解锁链条**
#    （见 routers/learn.py::_statuses）。这样新插入的课不会把老学生
#    已经解锁的课重新锁上，也不会自己卡在链条末端学不到。
_PYTHON: list[dict] = (BASICS + PY_CORE + ADVANCED + PY_OOP + PY_EXTRA
                       + AGENT + ENG_ADV + AI_ADV)
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
    """同科目里的下一课；已经是该链最后一课就返回 None。

    主线课和补充课**各自成链**：
    - 主线课的下一条只会在主线课里找 —— 否则补进来的课会插队到正常学习路径中间；
    - 补充课的下一条也只在补充课里找，这样「补充课」整体读起来是一条支线。
    """
    point = BY_CODE.get(code)
    if not point:
        return None
    supp = bool(point.get("supplementary"))
    codes = [p["code"] for p in BY_SUBJECT[point["subject"]]
             if bool(p.get("supplementary")) == supp]
    i = codes.index(code)
    return codes[i + 1] if i + 1 < len(codes) else None
