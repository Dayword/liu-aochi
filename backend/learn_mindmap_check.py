"""面试知识树自检：跑通才允许上线。

检查项（任一条不过就退出码 1）：
  1. 12 个科目和课程注册表完全一致（不多不少不写错名）
  2. 每科有 intro、branches 非空、每个分支 items 非空
  3. 同一科目内分支名不重复、知识点不重复
  4. 知识点 code 必须真实存在于 BY_CODE（写错一个就点不动）
  5. hot 只能是 1 / 2 / 3
  6. 文本长度合理（太长的字在图上会把版式撑烂）
  7. 每条都有 kp（思维导图节点）与 answer（面试考题答案），且长度在合理区间
  8. 同一分支内 kp 不重复（图上会出现两个一模一样的节点）

顺带输出覆盖率报告：每科有多少门课被这棵树引用到 —— 这个数字是给补课用的，
不是给面试看的，所以只打印不判定。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.seed.learn import BY_CODE, BY_SUBJECT, SUBJECTS  # noqa: E402
from app.seed.learn_mindmap import MINDMAPS  # noqa: E402

MAX_NAME = 52      # 题干上限（汉字数），超过在窄屏会折三行
MAX_BRANCH = 12    # 分支名上限
MAX_KP = 16        # 知识点标签上限（有效宽度：汉字 1 / 英文 0.55）
MIN_ANSWER = 20    # 答案下限：太短等于没答
MAX_ANSWER = 110   # 答案上限：说好「简短」，超了就是背作文
HOTS = {1, 2, 3}


def width(s: str) -> float:
    """按有效宽度算（汉字 1、英文数字 0.55），和中英混排的实际占位一致。"""
    return sum(1.0 if ord(c) > 127 else 0.55 for c in s)

errs: list[str] = []
warns: list[str] = []


def check_subjects() -> None:
    got, want = set(MINDMAPS), set(SUBJECTS)
    for name in sorted(want - got):
        errs.append(f"缺科目：{name} 没有知识树")
    for name in sorted(got - want):
        errs.append(f"多余科目：{name} 不在课程注册表里")


def check_tree(subject: str) -> None:
    tree = MINDMAPS[subject]
    intro = (tree.get("intro") or "").strip()
    if not intro:
        errs.append(f"{subject}：intro 为空")
    elif len(intro) > 90:
        warns.append(f"{subject}：intro {len(intro)} 字，偏长（建议 ≤90）")

    branches = tree.get("branches") or []
    if not branches:
        errs.append(f"{subject}：branches 为空")
        return

    seen_branch: set[str] = set()
    for bi, br in enumerate(branches, 1):
        bname = (br.get("name") or "").strip()
        if not bname:
            errs.append(f"{subject} 第 {bi} 个分支名为空")
            continue
        if len(bname) > MAX_BRANCH:
            errs.append(f"{subject} / {bname}：分支名 {len(bname)} 字，超过 {MAX_BRANCH}")
        if bname in seen_branch:
            errs.append(f"{subject}：分支名重复 -> {bname}")
        seen_branch.add(bname)

        items = br.get("items") or []
        if not items:
            errs.append(f"{subject} / {bname}：没有知识点")
            continue

        seen_item: set[str] = set()
        seen_kp: set[str] = set()
        for it in items:
            name = (it.get("name") or "").strip()
            if not name:
                errs.append(f"{subject} / {bname}：有空知识点")
                continue
            if len(name) > MAX_NAME:
                errs.append(f"{subject} / {bname}：知识点 {len(name)} 字超限 -> {name}")
            if name in seen_item:
                errs.append(f"{subject} / {bname}：知识点重复 -> {name}")
            seen_item.add(name)

            code = it.get("code")
            if code is not None:
                if code not in BY_CODE:
                    errs.append(f"{subject} / {bname}：code 不存在 -> {code}（{name}）")
                elif BY_CODE[code]["subject"] != subject:
                    # 不判错：跨科引用是故意的（如数据结构引 RAG 的向量库课）
                    pass

            if it.get("hot") not in HOTS:
                errs.append(f"{subject} / {bname}：hot 非法 -> {it.get('hot')}（{name}）")

            kp = (it.get("kp") or "").strip()
            if not kp:
                errs.append(f"{subject} / {bname}：缺知识点标签 kp（{name}）")
            else:
                if width(kp) > MAX_KP:
                    errs.append(f"{subject} / {bname}：kp 有效宽度 {width(kp):.1f} 超过 {MAX_KP} -> {kp}")
                if kp in seen_kp:
                    errs.append(f"{subject} / {bname}：kp 重复 -> {kp}")
                seen_kp.add(kp)

            ans = (it.get("answer") or "").strip()
            if not ans:
                errs.append(f"{subject} / {bname}：缺标准答案（{name}）")
            elif not (MIN_ANSWER <= len(ans) <= MAX_ANSWER):
                errs.append(f"{subject} / {bname}：答案 {len(ans)} 字，超出 {MIN_ANSWER}~{MAX_ANSWER}（{name}）")


def report() -> None:
    total_items = 0
    total_hot3 = 0
    total_nocode = 0
    print(f"{'科目':<14}{'分支':>4}{'知识点':>7}{'必问':>5}{'无课':>5}{'覆盖课程':>9}{'有答案':>6}")
    print("-" * 58)
    for subject in SUBJECTS:
        tree = MINDMAPS.get(subject) or {}
        brs = tree.get("branches") or []
        items = [it for br in brs for it in (br.get("items") or [])]
        used = {it.get("code") for it in items if it.get("code")}
        lessons = BY_SUBJECT[subject]
        hit = sum(1 for p in lessons if p["code"] in used)
        hot3 = sum(1 for it in items if it.get("hot") == 3)
        nocode = sum(1 for it in items if not it.get("code"))
        answered = sum(1 for it in items if (it.get("answer") or "").strip())
        total_items += len(items)
        total_hot3 += hot3
        total_nocode += nocode
        print(f"{subject:<14}{len(brs):>4}{len(items):>7}{hot3:>5}{nocode:>5}{hit:>6}/{len(lessons):<3}{answered:>6}")
    print("-" * 58)
    print(f"合计：{total_items} 个知识点，其中必问 {total_hot3}，暂无课程 {total_nocode}")

    # 全站未被任何树引用的课：可能是漏挂，也可能是纯练习课
    all_used = {it.get("code") for t in MINDMAPS.values() for br in t["branches"]
                for it in br["items"] if it.get("code")}
    orphan = [p["code"] for p in BY_CODE.values() if p["code"] not in all_used]
    if orphan:
        print(f"\n未被任何知识树引用的课（{len(orphan)} 门）：{', '.join(orphan[:20])}")


def main() -> int:
    check_subjects()
    for subject in MINDMAPS:
        check_tree(subject)
    report()
    if warns:
        print("\n警告：")
        for w in warns:
            print(f"  ! {w}")
    if errs:
        print(f"\n错误 {len(errs)} 条：")
        for e in errs:
            print(f"  x {e}")
        return 1
    print("\n全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
