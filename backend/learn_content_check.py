"""引导式学习内容自检：防止「课程里的示例代码能直接过判定」这类事故。

背景：判定逻辑是「学生代码 + checker → 看有没有 __PASS__」。整套课程里
`example` 是给学生看的示例（前端**默认可见**，不用点），`starter` 是编辑器的初始内容
—— 这两个**绝对不能**通过自己的 checker，否则等于把答案直接发出去。
历史上真出现过 9 处这种情况，所以固化成脚本。

除了「答案泄漏」，还会挡住另外三类会直接坑到学生的问题：
  1. `example` 自己跑不通（比如用了沙箱黑名单里的 os / pathlib）—— 学生照着抄必然报错
  2. `example_output` 和实际输出不一致 —— 学生看到的是假的「运行结果」
  3. 有动手任务却没有判定方式（既无 checker 也无 cases）—— 学生写完点不动

**只统计、不判错**的风格项（易错点条数、习题组合等）：历史课与新补充课的写法本来
就不完全统一，硬卡会把 100 多条噪音混进来，反而淹没真问题。这里只做松检查：
条数太少、第一题不是选择题这类明显异常才提示。

用法：
    cd backend && python learn_content_check.py
退出码 0 = 没有阻塞性问题，1 = 有课程不合格（可直接挂到 CI）。
"""
import sys

sys.path.insert(0, ".")

from app.seed import learn  # noqa: E402
from app.services.code_runner import run_python  # noqa: E402

REQUIRED = ["code", "stage", "title", "summary", "definition", "plain", "example",
            "example_output", "pitfalls", "task", "hint", "checker", "quizzes"]
# 能自动判分的客观题类型（short / applied 是主观题，只做参考）
AUTO_GRADED = {"choice", "judge", "blank"}
# 自检只关心「代码对不对」，不关心「跑得快不快」，所以给一个宽松的超时：
# numpy / pandas 首次导入本身就要一秒多，用生产那个 5s 会随机误报。
CHECK_TIMEOUT = 30

errors: list[str] = []
notes: list[str] = []
checked = 0
supplementary = 0
quiz_shapes: set[tuple] = set()
pitfall_counts: set[int] = set()

for point in learn.CURRICULUM:
    code = point.get("code", "?")
    runner = point.get("runner") or "python"
    # SQL 科目的判定走 sql_runner，不在这里检查
    if runner != "python":
        continue
    checked += 1
    if point.get("supplementary"):
        supplementary += 1

    miss = [k for k in REQUIRED if k not in point]
    if miss:
        errors.append(f"{code}: 缺字段 {miss}")
        continue

    quizzes = point["quizzes"]
    quiz_shapes.add(tuple(q["type"] for q in quizzes))
    pitfall_counts.add(len(point["pitfalls"]))
    if len(point["pitfalls"]) < 4:
        notes.append(f"{code}: 易错点只有 {len(point['pitfalls'])} 条（新课建议 4 条以上）")
    if len(quizzes) < 3:
        notes.append(f"{code}: 习题只有 {len(quizzes)} 道（建议 3 道以上）")
    elif quizzes[0]["type"] != "choice":
        notes.append(f"{code}: 第一道习题是 {quizzes[0]['type']}（习惯上从选择题开始）")
    elif not any(q["type"] in AUTO_GRADED for q in quizzes):
        notes.append(f"{code}: 没有一道能自动判分的客观题")

    # 判定方式有两种：新版用 checker（断言），早期课程用 cases（比对输出）
    checker = point.get("checker")
    cases = point.get("cases") or []
    has_task = bool(point.get("task"))

    if not checker and not cases:
        if has_task:
            errors.append(f"{code}: 有动手任务却没有判定方式（checker / cases 都为空）")
        continue

    if checker:
        if "except NameError" not in checker:
            errors.append(f"{code}: checker 缺少 except NameError 分支"
                          "（学生没定义函数时会读到一个毫无线索的 NameError）")
        try:
            compile(checker, f"<{code}>", "exec")
        except SyntaxError as e:
            errors.append(f"{code}: checker 语法错误 {e}")
            continue

        def verdict(src: str) -> bool:
            """这份代码能不能通过这一课的判定（True = 通过了）。"""
            r = run_python(point.get("setup", "") + src + "\n\n" + checker,
                           timeout=CHECK_TIMEOUT)
            return "__PASS__" in r["stdout"]
    else:
        def verdict(src: str) -> bool:
            """cases 判定：每一组用例的输出都要与 expect_stdout 完全一致。"""
            for c in cases:
                r = run_python((c.get("setup") or "") + src, timeout=CHECK_TIMEOUT)
                if r["exit_code"] != 0:
                    return False
                if r["stdout"].strip() != (c.get("expect_stdout") or "").strip():
                    return False
            return True

    if verdict(point["starter"]):
        errors.append(f"{code}: ★ starter 能通过判定 —— 等于把答案发给学生了")
    if verdict(point["example"]):
        errors.append(f"{code}: ★ example 能通过判定 —— 等于把答案发给学生了")

    only = run_python(point["example"], timeout=CHECK_TIMEOUT)
    if only["exit_code"] != 0:
        errors.append(f"{code}: example 自己跑不通 —— {only['stderr'].strip()[-140:]}")
    elif only["stdout"].strip() != point["example_output"].strip():
        errors.append(f"{code}: example_output 与实际输出不符\n"
                      f"    写的={point['example_output']!r}\n"
                      f"    实测={only['stdout'].strip()!r}")

print(f"检查了 {checked} 个 Python 知识点（共 {len(learn.CURRICULUM)} 个知识点）")
print(f"其中补充课 {supplementary} 个（不参与主线解锁链条）")
print(f"习题组合 {len(quiz_shapes)} 种，易错点条数分布 {sorted(pitfall_counts)}")

if notes:
    print(f"\n提示 {len(notes)} 条（风格问题，不影响退出码）：")
    for n in notes:
        print("  -", n)

if errors:
    print(f"\n❌ {len(errors)} 处问题：")
    for e in errors:
        print("  -", e)
    sys.exit(1)

print("\n✅ 全部通过：没有课程泄漏答案，示例都能跑、输出都对，任务都有判定")
