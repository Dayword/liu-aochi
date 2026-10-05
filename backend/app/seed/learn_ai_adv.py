"""阶段：AI Agent 进阶（补充课）。

这是「AI Agent 开发」主干课之后的延续：ReAct 循环、工具调用、记忆都已经在主线里讲过，
这里补上两个真正决定 Agent 能不能上线的工程问题 ——
怎么量化地知道它「这一版比上一版更好」（评测），以及一个 Agent 搞不定时怎么拆成多个角色协作（多 Agent 编排）。

每个知识点包含：定义、通俗理解、例子、易错点，以及
- 动手题（checker 判定）
- 习题 quizzes（choice / judge / blank）

supplementary=True 表示这是「补充课」：不参与引导式学习的主线解锁链条。
"""

EVAL_CHECKER = """
try:
    assert exact_match("  Yes ", "yes") is True, "exact_match 要先去首尾空格、再统一小写：'  Yes ' 和 'yes' 应该算完全匹配"
    assert exact_match("yes", "no") is False, "内容不同就应该返回 False"
    assert exact_match("", "") is True, "两个空串也算完全匹配（归一化后相等）"

    r = evaluate(["yes", "no", "maybe"], ["yes", "no", "yes"])
    assert r["total"] == 3, f"total 应该是条数 3，现在是 {r.get('total')!r}"
    assert r["correct"] == 2, f"correct 应该是完全匹配的条数 2（只有前两条对），现在是 {r.get('correct')!r}"
    assert r["accuracy"] == round(2 / 3, 3), f"accuracy 应该是四舍五入 3 位的 0.667，现在是 {r.get('accuracy')!r}"

    r0 = evaluate(["a", "b"], ["x", "y"])
    assert r0["total"] == 2, "全错时 total 依然要统计总条数"
    assert r0["correct"] == 0, "全错时 correct 应该是 0"
    assert r0["accuracy"] == 0.0, f"全错时 accuracy 应该是 0.0，现在是 {r0.get('accuracy')!r}"

    r8 = evaluate(["a", "b", "c", "d", "e"], ["a", "b", "c", "d", "x"])
    assert r8["accuracy"] == 0.8, f"5 条对 4 条，accuracy 应该是 0.8，现在是 {r8.get('accuracy')!r}"
    assert passes(r8, 0.8) is True, "准确率正好等于阈值 0.8 也算通过（判定条件是「大于等于」）"
    assert passes({"accuracy": 0.79}, 0.8) is False, "0.79 低于阈值 0.8，不应该通过"
    assert passes(r8) is True, "不传阈值时默认 0.8，0.8 应该通过"

    assert all_pass([True, True]) is True, "全部为 True 才返回 True"
    assert all_pass([True, False]) is False, "只要有一个 False 就不是全通过"
    assert all_pass([]) is False, "空列表这里约定返回 False —— 没有用例就不算通过，这是业务决策"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except (TypeError, KeyError, IndexError) as e:
    print("__FAIL__ 调用方式或返回结构不对：" + str(e))
"""

MULTIAGENT_CHECKER = """
try:
    # 场景一：第一稿就过关 —— 只调用一次 critic，返回原文和 1 轮
    r = reflect_loop("draft-OK", lambda t: "OK" in t, lambda t: t + "-1", 3)
    assert r == ("draft-OK", 1), f"第一稿就通过时应该返回 (原文, 1)，现在是 {r!r}"

    # 场景二：第三稿才过关 —— 轮数是「调用 critic 的次数」
    r2 = reflect_loop("draft", lambda t: t == "draft-1-1", lambda t: t + "-1", 3)
    assert r2 == ("draft-1-1", 3), f"第三稿才通过时应该返回 ('draft-1-1', 3)，现在是 {r2!r}"

    # 场景三：一直不过关，max_rounds=3 —— 必须正好修改 3 次，返回第 3 次修改后的文本
    calls = {"critic": 0, "reviser": 0}

    def never(t):
        calls["critic"] += 1
        return False

    def add_one(t):
        calls["reviser"] += 1
        return t + "-1"

    r3 = reflect_loop("d", never, add_one, 3)
    assert r3 == ("d-1-1-1", 3), f"一直不过关时应返回 (第 3 次修改后的文本, 3)，现在是 {r3!r}"
    assert calls["critic"] == 3, f"max_rounds=3 时 critic 应该被调用 3 次，实际 {calls['critic']} 次"
    assert calls["reviser"] == 3, f"max_rounds=3 时 reviser 应该被调用 3 次（不能多改也不能少改），实际 {calls['reviser']} 次"

    # 场景四：max_rounds=1 且一直不过关 —— 只允许改 1 次
    calls2 = {"reviser": 0}

    def add_one2(t):
        calls2["reviser"] += 1
        return t + "-1"

    r4 = reflect_loop("d", lambda t: False, add_one2, 1)
    assert r4 == ("d-1", 1), f"max_rounds=1 时应该返回 ('d-1', 1)，现在是 {r4!r}"
    assert calls2["reviser"] == 1, f"max_rounds=1 时 reviser 只能被调用 1 次，实际 {calls2['reviser']} 次"
    print("__PASS__")
except AssertionError as e:
    print("__FAIL__ " + str(e))
except NameError as e:
    print("__FAIL__ 还有名字没有定义：" + str(e))
except TypeError as e:
    print("__FAIL__ 参数或返回值形式不对：" + str(e))
"""

LESSONS: list[dict] = [
    {
        "code": "ai-eval",
        "stage": "AI Agent 进阶",
        "title": "Agent 评测（Evals）",
        "summary": "改完 prompt 是好是坏，得用固定评测集说了算",
        "supplementary": True,
        "definition": (
            "**Agent 评测（Evals）= 用一套固定的测试集，量化地判断这一版比上一版到底是变好还是变坏。**\n\n"
            "为什么不能靠「手点一下看它答得对不对」？因为大模型的输出是概率性的，"
            "而且改一个 prompt 常常**按下葫芦浮起瓢**：修好了 A 场景，又悄悄弄坏了 B 场景。"
            "只有**固定评测集 + 自动打分**，才能告诉你这次改动的净值是正是负。\n\n"
            "评测集的设计要点：\n"
            "- **固定**：每次评测都用同一批用例，分数才有可比性\n"
            "- **含回归用例**：把历史上踩过的坑（线上出过的 bug）都收进来，"
            "防止「已经修好的问题又复发」（回归）\n"
            "- **覆盖边界**：空输入、超长输入、对抗性输入、格式异常都要有\n\n"
            "常见指标：\n"
            "- **准确率 / 通过率**：正确条数 ÷ 总条数\n"
            "- **完全匹配率（exact match）**：输出和参考答案在归一化（去空格、统一大小写）后相等才算对\n"
            "- **业务规则指标**：比如「所有安全用例必须 100% 通过，一条都不许错」——"
            "这种「必须全部通过才算通过」的场景，要用类似 `all_pass` 的判定来卡\n\n"
            "**LLM-as-judge**（让一个模型给另一个模型的输出打分）：\n"
            "- 好处：能评价「回答是否礼貌、是否符合语气」这类**没有唯一标准答案**的主观质量，"
            "比字符串精确匹配灵活得多\n"
            "- 三大局限：① **评分漂移**（同一份答案两次打分可能不一样）；"
            "② **偏好长答案**（倾向于给更啰嗦的回答更高分）；"
            "③ **同一个模型评自己**（偏好自己的风格，不够客观）\n\n"
            "最后是**离线评测 + 线上监控**的闭环：离线用固定集打分做回归；"
            "线上埋点统计真实通过率、收集失败样本，把有价值的失败样本**回流进评测集**"
            "——这样评测集才会越用越贴近真实场景。"
        ),
        "plain": (
            "**评测就是给 Agent 出一套「模拟考」。**\n\n"
            "没有评测集时，你的上线流程是这样的：改完 prompt → 随手试几个例子 → 「好像没问题」→ 上线 → "
            "用户炸了。问题在于：**你试的那几个例子，不等于全部场景**。\n\n"
            "有了固定评测集，流程变成：改完 → 跑一遍 100 条用例 → 「从 82 分掉到 78 分」→ "
            "**数字告诉你这次改动其实变差了**，于是回滚。这就是评测的价值：把「感觉」变成「数字」。\n\n"
            "**为什么要保留历史 bug 的用例？** 因为你修 bug 时很容易连带弄坏别的地方。"
            "把每个真实踩过的坑都做成一条用例，下次改动如果又踩回去，评测会立刻报警——"
            "这就叫**回归测试**。\n\n"
            "**为什么要用模型当裁判？** 有些答案是没法精确比对的。比如让 Agent「给这段代码写个注释」，"
            "根本没有唯一参考答案，只能让另一个模型判断「写得清不清楚、准不准确」。"
            "但它不完美：同一份答案可能今天 8 分明天 7 分（评分漂移），而且它老是给啰嗦的长回答打高分。"
            "所以**关键指标还得靠人工标注校准，不能全信模型裁判**。\n\n"
            "**线上失败样本一定要捞回来**：真实用户问到的问题，比你自己拍脑袋想的用例有价值得多。\n\n"
            "还有一点容易被忽略：**「必须全部通过」和「按比例通过」是两回事**。"
            "像格式校验、安全合规这类用例，一条都不能错，写 `assert all_pass(...)`；"
            "而开放问答类用例用准确率衡量就够了。"
        ),
        "example": (
            "def same(a, b):\n"
            "    # 归一化：去首尾空格 + 统一小写，再逐字比较\n"
            "    return a.strip().lower() == b.strip().lower()\n"
            "\n"
            "cases = [\n"
            "    (\"  Yes \", \"yes\"),   # 应该算通过\n"
            "    (\"已退款\", \"已退款\"),  # 应该算通过\n"
            "    (\"no\", \"yes\"),       # 应该算失败\n"
            "]\n"
            "hits = sum(same(p, g) for p, g in cases)\n"
            "print(f\"通过 {hits}/{len(cases)}，准确率 {round(hits / len(cases), 3)}\")"
        ),
        "example_output": "通过 2/3，准确率 0.667",
        "pitfalls": [
            "**只手工试几条就上线**：每次只测当下想到的例子，改完「看着没问题」，其实悄悄弄坏了别的场景；只有固定评测集才能发现净值变负。",
            "**评测集里只有 happy path**：没有把历史踩过的坑做成回归用例，同一个 bug 会在后续改动中反复复发。",
            "**把 LLM-as-judge 的分数当绝对真理**：它评分会漂移、偏好长答案、同模型评自己会有偏，必须用人工标注定期校准。",
            "**只做离线评测、不做线上监控**：真实用户遇到的失败样本没有回流进评测集，评测集会越来越脱离现实，分数好看但线上照样出事。",
        ],
        "task": (
            "请实现下面 4 个函数：\n"
            "1. `exact_match(pred, gold)`：两边都先 `strip()` 再去掉大小写（`.lower()`）后比较，"
            "相同返回 `True`，否则返回 `False`。\n"
            "2. `evaluate(preds, golds)`：`preds` 和 `golds` 是等长的列表，逐条用 `exact_match` 判断，"
            "返回字典 `{\"total\": 总条数, \"correct\": 完全匹配的条数, \"accuracy\": 准确率（四舍五入保留 3 位）}`。\n"
            "3. `passes(report, threshold=0.8)`：`report` 是 `evaluate` 的返回值，"
            "当 `report[\"accuracy\"]` **大于等于** `threshold` 时返回 `True`，否则返回 `False`。\n"
            "4. `all_pass(results)`：`results` 是布尔列表，**全部为 `True`** 才返回 `True`；"
            "只要有一个 `False` 就返回 `False`；空列表返回 `False`"
            "（「没有用例算不算通过」是业务决策，这里约定不算）。"
        ),
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": (
            "归一化和比较可以一行搞定：\n"
            "```\ndef exact_match(pred, gold):\n"
            "    return pred.strip().lower() == gold.strip().lower()\n```\n"
            "统计用 `zip` 配生成器：`correct = sum(1 for p, g in zip(preds, golds) if exact_match(p, g))`。\n"
            "`all_pass` 要注意空列表：`return bool(results) and all(results)`（`all([])` 本身是 `True`，得先挡掉）。"
        ),
        "checker": EVAL_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "为什么评测集里要专门保留一批「历史踩过的坑」的用例？",
                "options": [
                    "防止已经修好的问题在后续改动中复发（回归测试）",
                    "让评测集看起来更长、更有说服力",
                    "可以提高模型回答的速度",
                    "能用更少的 token 完成评测",
                ],
                "answer_index": 0,
                "explanation": "改 prompt 常常修好 A 弄坏 B。把每个真实 bug 都固化成一条回归用例，下次踩回去时评测会立刻发现。",
            },
            {
                "type": "choice",
                "stem": "下面哪一条**不是** LLM-as-judge（让模型当裁判打分）的典型局限？",
                "options": [
                    "评分会漂移：同一份答案两次打分可能不一样",
                    "倾向于给更长的答案更高的分",
                    "用同一个模型评自己时，会偏向自己的风格",
                    "完全无法评价主观质量，只能做字符串精确匹配",
                ],
                "answer_index": 3,
                "explanation": "D 说反了 —— LLM-as-judge 最大的价值恰恰是能评主观质量（比如礼貌、语气）；A、B、C 才是它公认的三大局限。",
            },
            {
                "type": "judge",
                "stem": "一个 Agent 手工试几个例子都能跑通，就说明它已经可以上线了。",
                "answer": False,
                "explanation": "「看起来能跑」不等于「能上线」。手工试的几个例子覆盖不到全部场景，必须用固定评测集做量化回归，否则改动很容易悄悄弄坏别的场景。",
            },
            {
                "type": "blank",
                "stem": "补全「必须全部通过才算通过」，注意空列表要返回 False：\nreturn bool(results) and ___(results)",
                "answer": "all",
                "hint": "填一个内置函数名",
                "explanation": "`all(...)` 判断所有元素是否都为真；前面的 `bool(results)` 保证空列表时直接短路返回 False，而不是 `all([])` 的 True。",
            },
        ],
    },
    {
        "code": "ai-multiagent",
        "stage": "AI Agent 进阶",
        "title": "多 Agent 协作与编排",
        "summary": "一个 Agent 搞不定时，怎么拆成多个角色协作完成",
        "supplementary": True,
        "definition": (
            "**多 Agent 协作 = 把一个大任务拆给多个各有分工的 Agent，再用某种编排方式把它们组织起来。**\n\n"
            "单 Agent 的问题：当任务「又长、又需要多种能力」时（比如「调研资料 → 写代码 → 测试 → 写报告」），"
            "把所有工具和指令都塞进一个提示词里，模型会**顾此失彼**——注意力被稀释，哪一块都做不精。\n\n"
            "三种主流编排模式：\n\n"
            "1. **Plan-and-Execute（先计划再执行）**：先让一个 Agent 产出**计划**（步骤列表），再逐步执行。"
            "好处是计划可以**审阅、可以打断**——高风险操作可以先让人确认再动手。\n\n"
            "2. **Orchestrator-Worker（调度者-工人）**：一个 **orchestrator** 负责拆解任务、分派、汇总；"
            "多个 **worker** 各自处理一个子任务。适合**子任务彼此独立、可以并行**的场景。\n\n"
            "3. **Reflection / 自省循环**：**做 → 自我批判 → 改**，反复迭代，直到达标或到达轮次上限。"
            "相当于让模型给自己当 reviewer，通常能明显提升单次输出的质量。\n\n"
            "**为什么必须设轮次上限和终止条件？** 自省循环如果没有「达标就停」的判断，"
            "模型会陷入无限自我否定（永远觉得「还能更好」），既烧钱又永远停不下来。"
            "所以必须同时有：**终止条件**（critic 判断过关就立刻返回）+ **硬上限**（最多迭代 N 轮）。\n\n"
            "**多 Agent 的代价**（要清醒认识）：\n"
            "- **token 翻倍**：Agent 之间的每一次通信都是额外的模型调用\n"
            "- **延迟变长**：串行编排下，总耗时约等于各步之和\n"
            "- **错误沿链路放大**：上游的一个小错会被下游当成事实继续加工\n"
            "- **调试更难**：出错时要在多个 Agent 之间定位「到底是谁错了」\n\n"
            "**工程建议：能用「单 Agent + 好工具」解决的，就不要上多 Agent。** "
            "多 Agent 是复杂度和成本的显著上升，只有在单 Agent 确实顾不过来时才值得。"
        ),
        "plain": (
            "**打个比方**：单 Agent 像一个什么都要干的自由职业者，让他同时做调研、写代码、写报告，"
            "他会顾此失彼。多 Agent 像一个团队，有分工，但也得有人负责协调。\n\n"
            "**三种协作方式，对应三种现实场景**：\n"
            "- **Plan-and-Execute**：像装修先出方案。**先给你看图纸（计划），你点头了再施工**——"
            "好处是能审阅、能随时喊停，适合要花钱、要动线上数据的危险操作。\n"
            "- **Orchestrator-Worker**：像包工头发活。一个包工头把「刷墙、铺砖、装水电」分给三个工人**同时干**，"
            "最后汇总。适合子任务**互不依赖、可以并行**。\n"
            "- **Reflection**：像自己改作文。写完自己读一遍、挑刺、再改，读到满意为止。\n\n"
            "**但自省循环有个致命问题：什么时候算「满意」？** 如果模型永远觉得「还能更好」，"
            "它就会一直改下去。所以一定要设两道闸：**达标就停** + **最多改几轮**。"
            "少了任何一道，都可能变成烧钱的无底洞。\n\n"
            "这里还有个特别容易数错的细节：**「轮数」到底怎么算？** "
            "本课的约定是 —— **调用 critic（评审）的次数就是轮数**。"
            "第一稿拿去评一次就通过，那是 **1 轮**，不是 0 轮；第三稿才通过，就是 **3 轮**。\n\n"
            "**最后一句忠告**：团队不是越大越好。多个 Agent 意味着更多次模型调用（更贵）、更长的等待、"
            "更多出错的地方。**大多数任务，一个 Agent 配几个好用的工具就够了。**"
        ),
        "example": (
            "def refine(draft, good, fix, limit=3):\n"
            "    for i in range(limit):\n"
            "        if good(draft):          # 先评当前稿\n"
            "            return draft, i + 1  # i 从 0 开始，所以轮数是 i + 1\n"
            "        draft = fix(draft)       # 不过关就改一版\n"
            "    return draft, limit          # 到达上限，返回最后一稿\n"
            "\n"
            "def good(t):\n"
            "    return len(t) >= 6           # 够长才算过关\n"
            "\n"
            "def fix(t):\n"
            "    return t + \"更详细\"\n"
            "\n"
            "print(refine(\"AI\", good, fix, 5))   # 改到第 3 稿才够长"
        ),
        "example_output": "('AI更详细更详细', 3)",
        "pitfalls": [
            "**不设轮次上限或终止条件**：自省循环会一直「再改改」、无限自我否定，既烧钱又卡住；必须同时有「达标就停」和「最多 N 轮」。",
            "**单 Agent 能干却硬上多 Agent**：token 翻倍、延迟变长、调试更难，复杂度上升却未必换来收益；能用单 Agent + 好工具解决就别拆。",
            "**让多个 worker 共享可变状态**：并发写同一个对象会互相覆盖，出错后极难定位是谁改的。",
            "**中间结果不做校验**：上游 Agent 的一个小错会被下游当成事实继续加工，错误沿链路被放大，最后很难查清源头。",
        ],
        "task": (
            "实现 `reflect_loop(draft, critic, reviser, max_rounds=3)`（自省循环）：\n"
            "1. `critic(text)` 返回 `True` 表示这一稿过关；`reviser(text)` 返回修改后的新文本。\n"
            "2. 先评当前稿：`critic` 一过关就**立刻返回**，不要再多改一次。\n"
            "3. 不过关就调用 `reviser` 改一版；最多改 `max_rounds` 轮。\n"
            "4. 返回元组 `(最终文本, 实际经过的轮数)`。\n\n"
            "**轮数的定义（重点，别搞错）**：轮数 = **调用 `critic` 的次数**。\n"
            "- 第一稿就过 → 1 轮，返回 `(原文, 1)`\n"
            "- 第三稿才过 → 3 轮，返回 `(第三稿, 3)`\n"
            "- 一直不过、`max_rounds=3` → 返回 `(第 3 次修改后的文本, 3)`（正好改 3 次，不多不少）\n\n"
            "判定会用计数器统计 `critic` / `reviser` 各被调用了几次，请严格按上面的定义实现。"
        ),
        "setup": "",
        "starter": "# 在下面写出你的代码（删掉这行注释也没关系）\n",
        "hint": (
            "用一个变量记轮数，每轮先 `critic`、再决定要不要 `reviser`：\n"
            "```\ndef reflect_loop(draft, critic, reviser, max_rounds=3):\n"
            "    text = draft\n    rounds = 0\n"
            "    while rounds < max_rounds:\n        rounds += 1\n"
            "        if critic(text):\n            return text, rounds\n"
            "        text = reviser(text)\n    return text, rounds\n```"
        ),
        "checker": MULTIAGENT_CHECKER,
        "cases": [],
        "quizzes": [
            {
                "type": "choice",
                "stem": "哪种编排模式最适合「子任务彼此独立、可以并行处理」的批量任务？",
                "options": [
                    "Plan-and-Execute（先计划再执行）",
                    "Orchestrator-Worker（调度者-工人）",
                    "Reflection（自省循环）",
                    "单轮问答（一次调用直接返回）",
                ],
                "answer_index": 1,
                "explanation": "Orchestrator 把任务拆成互不依赖的子任务分给多个 worker 并行处理，再汇总；Plan-and-Execute 偏串行且有审阅点，Reflection 是单条输出的迭代打磨。",
            },
            {
                "type": "choice",
                "stem": "自省循环（Reflection）为什么必须设置轮次上限和终止条件？",
                "options": [
                    "否则模型会一直「再改改」、无限自我否定，既烧钱又卡住",
                    "为了让代码写得更短",
                    "为了把评测集缩小一些",
                    "因为模型 API 不允许连续多次调用",
                ],
                "answer_index": 0,
                "explanation": "如果没有「达标就停」和「最多 N 轮」这两道闸，模型会陷入无限迭代，成本失控且任务永远结束不了。",
            },
            {
                "type": "judge",
                "stem": "能用单个 Agent 加几个好工具解决的问题，也应该改成多 Agent 架构来提升效果。",
                "answer": False,
                "explanation": "多 Agent 会带来 token 翻倍、延迟变长、错误沿链路放大、调试更难等代价。能用单 Agent + 好工具解决就别拆 —— 这是本课的核心工程建议。",
            },
            {
                "type": "blank",
                "stem": "轮数按「调用 critic 的次数」计。那么第一稿就通过时，reflect_loop 应该返回的轮数是 ___",
                "answer": "1",
                "hint": "填一个数字",
                "explanation": "第一稿被拿去评了一次并通过，所以是 1 轮（不是 0 轮）。轮数的定义就是 critic 被调用的次数。",
            },
        ],
    },
]
