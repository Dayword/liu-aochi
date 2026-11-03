"""对话记忆的裁剪逻辑校验（滑动窗口 + 摘要注入）。

只测「怎么切」，不调模型、不连数据库，所以能当单元测试反复跑。
真实链路（摘要落库、后台任务）另有 verify 脚本覆盖。

用法：python chat_memory_check.py
退出码 0 = 全过。
"""
import sys

from app.ai import client as ai
from app.config import settings

FAILS: list[str] = []


def chk(name: str, ok: bool, extra: str = "") -> None:
    print(("  ok   " if ok else "  FAIL ") + name + ("" if ok else f"  ← {extra}"))
    if not ok:
        FAILS.append(name)


def make_history(turns: int, pad: int = 20) -> list[dict]:
    """造 turns 轮对话，内容带序号，方便断言「哪一轮被丢了」。"""
    out = []
    for i in range(1, turns + 1):
        out.append({"id": i * 2 - 1, "role": "user",
                    "content": f"第{i}轮提问：" + "内容" * pad})
        out.append({"id": i * 2, "role": "assistant",
                    "content": f"第{i}轮回答：" + "回答" * pad})
    return out


def check_shape() -> None:
    """内存紧张时的硬约束：起点必须是 user，末尾必须是 assistant，一轮不许拆开。"""
    hist = make_history(30)
    for budget in (200, 1000, 4000, 60000):
        # 显式放开条数上限，这里只验预算口径；条数上限由 check_max_turns 单独覆盖
        kept, dropped = ai.split_history(hist, token_budget=budget, max_turns=100)
        chk(f"budget={budget} 起点是 user", kept[0]["role"] == "user", kept[0]["role"])
        chk(f"budget={budget} 末尾是 assistant", kept[-1]["role"] == "assistant", kept[-1]["role"])
        chk(f"budget={budget} dropped+kept 等于原历史", dropped + kept == hist)
        # 每一轮必须成对出现
        pairs = len(kept) % 2 == 0
        chk(f"budget={budget} 保留条数为偶数（成轮）", pairs, f"kept={len(kept)}")


def check_budget() -> None:
    hist = make_history(30, pad=200)      # 每条约 420 字，一轮约 900 token
    kept_small, _ = ai.split_history(hist, token_budget=1000, max_turns=100)
    kept_big, _ = ai.split_history(hist, token_budget=100000, max_turns=100)
    chk("预算小 → 只留最近一两轮", len(kept_small) <= 4, f"kept={len(kept_small)}")
    chk("预算大 → 全部保留", len(kept_big) == len(hist), f"kept={len(kept_big)}")
    chk("预算越大保留越多", len(kept_small) < len(kept_big))


def check_max_turns() -> None:
    hist = make_history(40, pad=1)        # 短消息，纯靠条数上限截断
    kept, _ = ai.split_history(hist, token_budget=999999, max_turns=6)
    chk("条数上限生效", len(kept) == 12, f"kept={len(kept)}")
    chk("条数上限下起点仍是 user", kept[0]["role"] == "user")


def check_oversize_turn() -> None:
    """用户贴了一大段代码提问：这一轮自己就超预算，也必须留下（丢了等于没问）。"""
    hist = [{"id": 1, "role": "user", "content": "看这段代码：" + "x" * 20000},
            {"id": 2, "role": "assistant", "content": "这段代码的问题是……"}]
    kept, dropped = ai.split_history(hist, token_budget=100)
    chk("超预算的最近一轮仍保留", len(kept) == 2, f"kept={len(kept)}")
    chk("超长内容被掐中段", "省略" in kept[0]["content"], kept[0]["content"][:40])
    chk("没有内容被划进 dropped", dropped == [])


def check_orphan() -> None:
    """历史被截过、开头是孤立的 assistant：不能崩，也不能让它排到 kept 最前面。"""
    hist = [{"id": 1, "role": "assistant", "content": "（上一条回答，提问已丢失）"},
            {"id": 2, "role": "user", "content": "继续"},
            {"id": 3, "role": "assistant", "content": "好的"}]
    kept, dropped = ai.split_history(hist, token_budget=100000)
    chk("孤立 assistant 不影响成轮", kept[0]["role"] == "user", kept[0]["role"])
    chk("孤立 assistant 被归入 dropped", dropped and dropped[0]["role"] == "assistant")


def check_empty() -> None:
    kept, dropped = ai.split_history([], token_budget=1000)
    chk("空历史返回两个空列表", kept == [] and dropped == [])


def check_tokens() -> None:
    zh = ai.estimate_tokens("中文" * 100)      # 200 汉字
    en = ai.estimate_tokens("word " * 100)     # 500 字符
    chk("中文按 1 字 1 token 估", 200 <= zh <= 240, str(zh))
    chk("英文明显比同长度中文便宜", en < zh, f"en={en} zh={zh}")


def check_messages() -> None:
    """system 必须常驻首条，摘要只能进 system，不能冒充成一条对话。"""
    ai.knowledge_context = lambda db, m: ""      # 不连库
    hist = make_history(2)
    plain = ai.build_chat_messages(None, "学霸学长", "继续", hist)
    with_sum = ai.build_chat_messages(None, "学霸学长", "继续", hist, summary="用户叫小明，在做 RAG 项目")
    chk("system 恒在第 0 条", plain[0]["role"] == "system")
    chk("末尾是本次提问", plain[-1] == {"role": "user", "content": "继续"})
    chk("无摘要时不出现记忆段", "已知背景" not in plain[0]["content"])
    chk("有摘要时拼进 system", "已知背景" in with_sum[0]["content"]
        and "小明" in with_sum[0]["content"])
    chk("摘要不新增对话条数", len(plain) == len(with_sum), f"{len(plain)} vs {len(with_sum)}")
    chk("人设与语言约束仍在", ai.PYTHON_ONLY_RULE[:12] in with_sum[0]["content"])
    chk("历史原样带进 messages", plain[1:-1] == hist)

    # 首次越界那一轮：摘要还没压出来，必须让它承认「看不到」，而不是断言用户没说过
    gap_msg = ai.build_chat_messages(None, "学霸学长", "继续", hist, gap=True)
    chk("gap 提示已注入", "已被截断" in gap_msg[0]["content"])
    chk("gap 不许说「你没提过」", "你之前没有提过" in gap_msg[0]["content"])
    both = ai.build_chat_messages(None, "学霸学长", "继续", hist, summary="有摘要", gap=True)
    chk("有摘要时不叠加 gap 提示", "已被截断" not in both[0]["content"])


def check_config() -> None:
    chk("历史预算配置合理", settings.CHAT_HISTORY_TOKENS >= 2000, str(settings.CHAT_HISTORY_TOKENS))
    chk("摘要条数阈值 ≥2", settings.CHAT_SUMMARY_MIN_MSGS >= 2, str(settings.CHAT_SUMMARY_MIN_MSGS))


def main() -> int:
    print("== 形状（成轮、起点、拼接）")
    check_shape()
    print("== 预算")
    check_budget()
    print("== 条数上限")
    check_max_turns()
    print("== 超长单轮")
    check_oversize_turn()
    print("== 孤立 assistant")
    check_orphan()
    print("== 空历史")
    check_empty()
    print("== token 估算")
    check_tokens()
    print("== messages 组装")
    check_messages()
    print("== 配置")
    check_config()
    print()
    if FAILS:
        print(f"失败 {len(FAILS)} 项：{FAILS}")
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
