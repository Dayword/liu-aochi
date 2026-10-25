"""「项目实地」数据的公共结构。

每门课挂一条 `project` 记录，说明这个知识点在「鸭先知 · 游乐园智能体」
（D:/PythonProject/游乐场智能rag问答系统）里到底落在哪一行代码上。

两种 kind：

- ``used``   —— 项目里真的这么写了。给出 文件:行号 + 真实代码摘录。
- ``absent`` —— 项目里**没有**用这个知识点。说明它实际用了什么替代方案、
                以及什么场景下才真的需要它。

代码摘录一律从源文件复制，允许用 ``...`` 省略中间行，但**不许改写逻辑** ——
学生拿行号去对照时必须能对上。
"""

PROJECT_NAME = "鸭先知 · 游乐园智能体"
PROJECT_PATH = r"D:\PythonProject\游乐场智能rag问答系统"


def used(file: str, lines: str, snippet: str, where: str, why: str, quiz: list) -> dict:
    """知识点在项目里真实出现。"""
    return {
        "kind": "used",
        "file": file,
        "lines": lines,
        "snippet": snippet.strip("\n"),
        "where": where,
        "why": why,
        "quiz": quiz,
    }


def absent(snippet: str, where: str, why: str, quiz: list, file: str = "") -> dict:
    """知识点在项目里没出现（snippet 放替代方案的代码）。"""
    return {
        "kind": "absent",
        "file": file,
        "lines": "",
        "snippet": snippet.strip("\n") if snippet else "",
        "where": where,
        "why": why,
        "quiz": quiz,
    }


def choice(stem: str, options: list, answer: int, explain: str) -> dict:
    """单选题：answer 是正确选项的下标（从 0 开始）。"""
    return {
        "type": "choice",
        "stem": stem,
        "options": options,
        "answer": answer,
        "explain": explain,
    }


def judge(stem: str, answer: int, explain: str) -> dict:
    """判断题：answer 为 1 表示「对」，0 表示「错」。"""
    return {"type": "judge", "stem": stem, "answer": answer, "explain": explain}
