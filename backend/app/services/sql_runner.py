"""SQL 运行沙箱（本地演示版）。

用**内存 SQLite** 跑学生的 SQL：不落盘、每次都是全新的库，
学生无论写什么（哪怕 DROP TABLE）都影响不到别的请求。

建表与样例数据由课程内容自带（`sql_setup`），学生只负责写查询。
生产环境应按设计文档替换为隔离的 MySQL 实例或 Judge0。
"""
from __future__ import annotations

import re
import sqlite3
import unicodedata

MAX_SQL_SIZE = 8 * 1024

# SQLite 允许挂载外部文件，演示环境直接禁掉。
_BLOCKED = re.compile(r"\b(attach|detach)\b", re.IGNORECASE)

_SETUP_FAIL = "这道题的题目数据有问题，不是你的错 —— 请把这一课反馈给管理员。"


def _disp_len(s: str) -> int:
    """按显示宽度算长度：中日韩字符占两格，否则对齐会歪。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _split_statements(text: str) -> list[str]:
    """把一段 SQL 切成一条条语句。

    用 sqlite3.complete_statement 判断"这句写完了没有"，
    这样字符串字面量里的分号、注释里的分号都不会被误切。
    """
    out: list[str] = []
    buf = ""
    for line in text.splitlines(keepends=True):
        buf += line
        if sqlite3.complete_statement(buf):
            if buf.strip():
                out.append(buf.strip())
            buf = ""
    if buf.strip():
        out.append(buf.strip())
    return out


def _norm(v: object) -> object:
    """归一化单个值：3.0 和 3 应该算相等，bytes 转成字符串。"""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    if v is None:
        return "NULL"
    return v


def _row_key(row) -> tuple[str, ...]:
    return tuple(str(_norm(v)) for v in row)


def compare_rows(got: list, expect: list, ordered: bool) -> bool:
    """比对结果集。ordered=False 时按无序多重集比（行序不影响判分）。

    行列数、NULL、数值格式都会被比到 —— 多查一个字段也算错，
    这是为了逼学生把字段列清楚（面试里 SELECT * 是要被说的）。
    """
    g = [_row_key(r) for r in got]
    e = [_row_key(r) for r in expect]
    if len(g) != len(e):
        return False
    return g == e if ordered else sorted(g) == sorted(e)


def format_table(cols: list[str], rows: list, limit: int = 20) -> str:
    """把结果集渲染成对齐的文本表格，给前端「你的输出」用。"""
    if not cols:
        return "（这条 SQL 没有返回结果集）"
    body = [
        [("NULL" if v is None else str(v)) for v in r] for r in rows[:limit]
    ]
    widths = [
        max([_disp_len(cols[i])] + [_disp_len(r[i]) for r in body])
        for i in range(len(cols))
    ]

    def pad(cell: str, w: int) -> str:
        return cell + " " * (w - _disp_len(cell))

    def line(cells: list[str]) -> str:
        return " | ".join(pad(c, w) for c, w in zip(cells, widths)).rstrip()

    out = [line(cols), "-+-".join("-" * w for w in widths)]
    out += [line(r) for r in body]
    if len(rows) > limit:
        out.append(f"...（共 {len(rows)} 行，只显示前 {limit} 行）")
    if not rows:
        out.append("（空结果集）")
    return "\n".join(out)


def run_sql(setup_sql: str, user_sql: str, verify_sql: str = "") -> dict:
    """执行学生的 SQL。

    返回 {ok, rows, cols, error, setup_error, phase}。
    给了 `verify_sql`（用于"建表 / 插数"类题目）时，会先把学生的语句跑完，
    再跑这条固定查询，用它的结果去判分。

    `phase` 标明错误出在哪一段，调用方据此决定提示文案：
    - "user"   学生自己的语句就报错了 → 按错误类型给对症提示；
    - "verify" 学生的语句都跑通了，是固定校验查询失败 —— 说明"该建的没建出来"，
      **不能**报成"表名写错了"，那等于把学生引到完全无关的方向上去。
    """
    if len(user_sql.encode("utf-8")) > MAX_SQL_SIZE:
        return {"ok": False, "rows": [], "cols": [], "phase": "user",
                "error": "SQL 太长了，这次练习不需要这么多。"}
    if _BLOCKED.search(user_sql):
        return {"ok": False, "rows": [], "cols": [], "phase": "user",
                "error": "出于演示环境安全考虑，不支持 ATTACH / DETACH。"}

    conn = sqlite3.connect(":memory:")
    try:
        try:
            conn.executescript(setup_sql or "")
        except sqlite3.Error:
            return {"ok": False, "rows": [], "cols": [], "phase": "",
                    "error": "", "setup_error": _SETUP_FAIL}

        cols: list[str] = []
        rows: list = []
        # ---- 第一段：单独跑学生的语句，报错一定是他自己写的问题 ----
        try:
            for stmt in _split_statements(user_sql):
                cur = conn.execute(stmt)
                if cur.description:
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
        except sqlite3.Error as e:
            return {"ok": False, "rows": [], "cols": [], "setup_error": "",
                    "error": f"{type(e).__name__}: {e}", "phase": "user"}

        # ---- 第二段：固定校验查询（仅建表/插数类题目有） ----
        if verify_sql:
            try:
                cur = conn.execute(verify_sql)
            except sqlite3.Error as e:
                return {"ok": False, "rows": [], "cols": [], "setup_error": "",
                        "error": f"{type(e).__name__}: {e}", "phase": "verify"}
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()

        return {"ok": True, "rows": rows, "cols": cols, "error": "",
                "setup_error": "", "phase": ""}
    except sqlite3.Error as e:
        # 兜底：上面两段之外的异常，理论上走不到。
        return {"ok": False, "rows": [], "cols": [], "setup_error": "",
                "error": f"{type(e).__name__}: {e}", "phase": "user"}
    finally:
        conn.close()
