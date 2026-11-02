"""面试知识树总入口：12 棵科目树，共 60 个分支 / 357 个考点。

数据按科目拆在四个文件里（每科都带 `intro` 与 `branches`）：

    learn_mm_py.py     Python（11 个面试考察维度）
    learn_mm_core.py   MySQL / Redis / 计算机网络 / 数据结构 / 操作系统
    learn_mm_ai.py     数据分析与处理 / Transformer / RAG 检索工程
    learn_mm_eng.py    后端服务工程 / 多模态与部署 / AI 工程质量

每个考点是一条 dict：

    name   考官的问法（「面试考题」页的题干）
    kp     浓缩成名词的知识点标签（「思维导图」页的节点，如 装饰器 / GIL / 最左前缀）
    answer 40~80 字的标准答案；能落到鸭先知项目的地方直接带项目细节
    code   对应 `seed/learn_*.py` 里的课程 code，点一下能跳过去学
    hot    3 = 必问 / 2 = 常问 / 1 = 纵深

`code` 写 None 表示「面试会问、但站内还没对应课程」，页面上标成「待补」，
不假装有 —— 这个字段让地图能反过来暴露课程空缺，补课按图补。

⚠️ 为什么按「面试考察维度」而不是照抄课程 stage：课程的 stage 是教学顺序
（Python 基础 → 进阶 → 工程 → Agent），面试官脑子里的结构是另一套
（可变性 → 容器 → 并发 → 工程）。两套结构对不上，照课程生成出来的图
只是目录换了个画法，学生看不出「这题会怎么问」。

⚠️ 改完必须跑 `python learn_mindmap_check.py`（在 backend 目录下），
校验 code 真实存在、答案长度、kp 不为空，退出码 0 才算过。
"""

from .learn_mm_ai import TREES as _AI
from .learn_mm_core import TREES as _CORE
from .learn_mm_eng import TREES as _ENG
from .learn_mm_py import TREES as _PY

# 顺序无关紧要：路由按 seed/learn.py 的 SUBJECTS 顺序去取
MINDMAPS: dict[str, dict] = {**_PY, **_CORE, **_AI, **_ENG}
