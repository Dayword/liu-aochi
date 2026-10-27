"""校验手绘知识图数据（`app/seed/learn_sketch.py`）。

跑法：`cd backend && python learn_sketch_check.py`（退出码 0 通过 / 1 有问题）

挡的是会真的把页面画坏的那几类问题：
1. `code` 指向不存在的课（点了跳到 404 或者没反应）；
2. `zone` / `kind` 写了渲染器不认识的词（节点会跑到画布中央叠在一起）；
3. 边引用了不存在的节点（整条线画不出来）；
4. 同一圈里两个节点抢同一个方位（必然重叠）；
5. 标签太长（中文超过 10 字会顶出圈）。
字数与「一句话」长度只提示不判失败，避免为了凑格式牺牲表达。
"""
import sys

from app.seed.learn import BY_CODE
from app.seed.learn_sketch import SKETCHES

ZONES = {"t", "tr", "r", "br", "b", "bl", "l", "tl"}
KINDS = {"core", "prev", "next", "side"}
MAX_LABEL = 10
MAX_ONELINER = 78


def eff_width(s: str) -> float:
    """按「一个汉字宽 = 1、一个英文字符宽 ≈ 0.55」估节点宽度。

    渲染器用的是同一套估算，所以这里按有效宽度判断，而不是字符数 ——
    否则 `break/continue` 这种英文标签会被误判成超长。
    """
    return sum(1.0 if ord(ch) > 0x2E80 else 0.55 for ch in s)

errors: list[str] = []
warns: list[str] = []

for code, sk in SKETCHES.items():
    if code not in BY_CODE:
        errors.append(f"{code}: 课程不存在（不是 BY_CODE 里的 code）")
        continue
    oneliner = (sk.get("oneliner") or "").strip()
    if not oneliner:
        errors.append(f"{code}: 缺 oneliner")
    elif eff_width(oneliner) > MAX_ONELINER:
        warns.append(f"{code}: oneliner 宽 {eff_width(oneliner):.0f}，偏长（建议 ≤{MAX_ONELINER}）")
    if not (sk.get("center") or "").strip():
        errors.append(f"{code}: 缺 center")

    ids = {"center"}
    seen_zone: dict[tuple[str, str], str] = {}
    core_n = 0
    for n in sk.get("nodes") or []:
        nid = n.get("id") or ""
        if not nid or nid == "center":
            errors.append(f"{code}: 节点 id 缺失或用了保留字 center")
            continue
        if nid in ids:
            errors.append(f"{code}: 节点 id 重复 {nid}")
        ids.add(nid)
        if n.get("kind") not in KINDS:
            errors.append(f"{code}/{nid}: kind={n.get('kind')!r} 不认识")
        if n.get("zone") not in ZONES:
            errors.append(f"{code}/{nid}: zone={n.get('zone')!r} 不认识")
        else:
            ring = "core" if n.get("kind") == "core" else "out"
            key = (ring, n["zone"])
            if key in seen_zone:
                errors.append(f"{code}: {nid} 和 {seen_zone[key]} 抢同一个方位 {n['zone']}")
            seen_zone[key] = nid
        if n.get("kind") == "core":
            core_n += 1
        label = n.get("label") or ""
        if not label:
            errors.append(f"{code}/{nid}: 缺 label")
        elif eff_width(label) > MAX_LABEL:
            warns.append(f"{code}/{nid}: 标签「{label}」宽 {eff_width(label):.1f}，超过 {MAX_LABEL}")
        target = n.get("code")
        if target and target not in BY_CODE:
            errors.append(f"{code}/{nid}: code={target} 指向不存在的课程")
        if target and target == code:
            errors.append(f"{code}/{nid}: code 指向自己")
    if core_n < 2:
        errors.append(f"{code}: 本课知识点只有 {core_n} 个，至少 2 个")

    for e in sk.get("edges") or []:
        for end in (e.get("a"), e.get("b")):
            if end not in ids:
                errors.append(f"{code}: 边 {e.get('a')}→{e.get('b')} 引用了不存在的节点 {end!r}")
        if e.get("a") == e.get("b"):
            errors.append(f"{code}: 自环边 {e.get('a')}")

# 覆盖率提示：还有多少课没铺
missing = [c for c in BY_CODE if c not in SKETCHES]
print(f"已铺 {len(SKETCHES)} 课 / 共 {len(BY_CODE)} 课，未铺 {len(missing)} 课")
for w in warns[:12]:
    print("  提示", w)
if len(warns) > 12:
    print(f"  …… 另有 {len(warns) - 12} 条提示")
for e in errors[:20]:
    print("  错误", e)
if len(errors) > 20:
    print(f"  …… 另有 {len(errors) - 20} 条错误")
print("RESULT", "PASS" if not errors else f"FAIL ({len(errors)} 个问题)")
sys.exit(0 if not errors else 1)
