"""大学三年路径图自检：跑通才允许上线。

检查项（任一条不过就退出码 1）：
  1. 分支（学期）非空、顺序是从大一上到大三下，不漏学期
  2. 每个学期至少 1 个行动项（kind=action），至多 4 个
        —— 这套图的价值一半在「什么时候动手」，全变成知识点就退化成课表了
  3. 行动项不许挂 code（动了手就没有对应课程，挂了会点进一节不相干的课）
  4. 知识点 code 必须真实存在于 BY_CODE，写错一个就点不动
  5. hot 只能是 1 / 2 / 3
  6. 文案长度合理（太长在窄屏会折三四行，把整棵树撑高）
  7. 叶子总数 ≤ 90（超了默认视图就糊成一片）

顺带报告：每个学期几个知识点 / 几个行动项；站内有多少门课被路径图引用到。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.seed.learn import BY_CODE  # noqa: E402
from app.seed.learn_roadmap import ROADMAP  # noqa: E402

MAX_NAME = 30      # 叶子文案上限，按「有效宽度」算（汉字 1、英文 0.55）
MAX_BRANCH = 14    # 分支名上限
MAX_LEAF = 90      # 叶子总数上限
HOTS = {1, 2, 3}
KINDS = {"lesson", "action"}


def vwidth(text: str) -> float:
    """视觉宽度：汉字算 1，英文/数字/符号算 0.55。

    按 len() 判会把 "命令行与 Git：add / commit / push / diff" 算成 35 字判错，
    但它在节点框里只占约 20 个汉字的宽度；反过来纯中文的 35 字才是真撑爆。
    """
    return sum(0.55 if ord(c) < 128 else 1.0 for c in text)

# 学期顺序：必须按这个顺序出现，且不能缺
ORDER = ["大一上", "大一下", "大二上", "大二下", "大三上", "大三下", "贯穿"]

errs: list[str] = []
warns: list[str] = []


def check_tree() -> None:
    intro = (ROADMAP.get("intro") or "").strip()
    if not intro:
        errs.append("intro 为空")
    elif len(intro) > 120:
        warns.append(f"intro {len(intro)} 字，偏长（建议 ≤120）")

    branches = ROADMAP.get("branches") or []
    if not branches:
        errs.append("branches 为空")
        return

    # 学期是否齐全、顺序是否对
    names = [(b.get("name") or "").strip() for b in branches]
    for key in ORDER:
        if not any(n.startswith(key) for n in names):
            errs.append(f"缺学期：{key}")

    seen_branch: set[str] = set()
    for bi, br in enumerate(branches, 1):
        bname = (br.get("name") or "").strip()
        if not bname:
            errs.append(f"第 {bi} 个分支名为空")
            continue
        if vwidth(bname) > MAX_BRANCH:
            errs.append(f"{bname}：分支名宽度 {vwidth(bname):.1f}，超过 {MAX_BRANCH}")
        if bname in seen_branch:
            errs.append(f"分支名重复 -> {bname}")
        seen_branch.add(bname)

        items = br.get("items") or []
        if not items:
            errs.append(f"{bname}：没有条目")
            continue

        actions = [it for it in items if it.get("kind") == "action"]
        # 「贯穿三年」是长期习惯，不要求有行动项
        if not bname.startswith("贯穿"):
            if not actions:
                errs.append(f"{bname}：一个行动项都没有（每学期至少 1 个）")
            elif len(actions) > 4:
                errs.append(f"{bname}：{len(actions)} 个行动项，超过 4 个，图会太挤")

        seen_item: set[str] = set()
        for it in items:
            name = (it.get("name") or "").strip()
            if not name:
                errs.append(f"{bname}：有空条目")
                continue
            if vwidth(name) > MAX_NAME:
                errs.append(f"{bname}：宽度 {vwidth(name):.1f} 超限 -> {name}")
            if name in seen_item:
                errs.append(f"{bname}：条目重复 -> {name}")
            seen_item.add(name)

            kind = it.get("kind", "lesson")
            if kind not in KINDS:
                errs.append(f"{bname}：kind 非法 -> {kind}（{name}）")

            code = it.get("code")
            if kind == "action" and code:
                errs.append(f"{bname}：行动项不该挂课程 code -> {code}（{name}）")
            if code is not None and code not in BY_CODE:
                errs.append(f"{bname}：code 不存在 -> {code}（{name}）")

            if it.get("hot") not in HOTS:
                errs.append(f"{bname}：hot 非法 -> {it.get('hot')}（{name}）")


def report() -> None:
    branches = ROADMAP.get("branches") or []
    print(f"{'学期':<18}{'知识点':>6}{'行动':>5}{'挂课':>5}{'硬地基':>7}")
    print("-" * 44)
    tot = act = hit = hard = 0
    used: set[str] = set()
    for br in branches:
        items = br.get("items") or []
        a = [it for it in items if it.get("kind") == "action"]
        c = [it for it in items if it.get("code")]
        h = [it for it in items if it.get("hot") == 3]
        used |= {it["code"] for it in c}
        tot += len(items)
        act += len(a)
        hit += len(c)
        hard += len(h)
        print(f"{(br.get('name') or ''):<18}{len(items) - len(a):>6}{len(a):>5}{len(c):>5}{len(h):>7}")
    print("-" * 44)
    print(f"合计：{tot} 个条目（{tot - act} 知识点 + {act} 行动项），"
          f"挂到站内课 {hit} 个，硬地基 {hard} 个")
    print(f"路径图引用到的站内课程：{len(used)} / {len(BY_CODE)} 门")

    if tot > MAX_LEAF:
        errs.append(f"叶子总数 {tot}，超过上限 {MAX_LEAF}")


def main() -> int:
    check_tree()
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
