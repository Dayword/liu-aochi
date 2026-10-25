"""把「鸭先知 · 游乐园智能体」的真实代码挂到每一门课上。

用法：`learn.py` 组装完 CURRICULUM 后调用 `attach(CURRICULUM)`，
每门课会多出一个 `project` 字段（结构见 learn_project_base）。

覆盖情况：
- `kind == "used"`   —— 项目里真的有这段实现，讲解指到 文件:行号；
- `kind == "absent"` —— 项目里没用这个知识点，讲清它用了什么替代方案、什么场景才需要。

两种都写，是为了不让学生产生「我学的每个知识点项目里都用了」的错觉。
"""

from .learn_project_be_mm import REFS as _BE_MM
from .learn_project_cs import REFS as _CS
from .learn_project_db import REFS as _DB
from .learn_project_eng import REFS as _ENG
from .learn_project_net import REFS as _NET
from .learn_project_py import REFS as _PY
from .learn_project_rag import REFS as _RAG

REFS: dict[str, dict] = {**_PY, **_ENG, **_DB, **_CS, **_NET, **_RAG, **_BE_MM}


def attach(curriculum: list[dict]) -> dict:
    """把 project 字段写进每门课；返回覆盖统计，便于自检脚本核对。"""
    used = absent = 0
    for point in curriculum:
        ref = REFS.get(point["code"])
        if not ref:
            continue
        point["project"] = ref
        if ref["kind"] == "used":
            used += 1
        else:
            absent += 1
    return {"used": used, "absent": absent, "total": len(REFS)}
