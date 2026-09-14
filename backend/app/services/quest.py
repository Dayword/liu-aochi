"""闯关核心逻辑：题目选取、难度自适应、答题判定、结算。"""
from __future__ import annotations

import random
import time
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models import (Character, Level, Question, User, UserLevelProgress,
                      WrongAnswer)
from . import growth

RUNS: dict[str, dict] = {}  # run_id -> 运行态（内存态，重启自动清空）


def start_run(db: Session, user: User, level: Level, mode: str = "normal",
              wrong_ids: list[int] | None = None) -> dict:
    run_id = uuid.uuid4().hex[:12]
    progress = db.query(UserLevelProgress).filter(
        UserLevelProgress.user_id == user.id,
        UserLevelProgress.level_code == level.code).first()
    attempts = progress.attempts if progress else 0

    # 选取题目：优先按关卡 tags + 难度，mode 决定规则
    qids = _pick_questions(db, level, mode, wrong_ids or [])
    if not qids:
        raise ValueError("该关卡暂无可用题目")

    char = user.character
    hp = char.max_hp if mode == "speed" else level.hp
    RUNS[run_id] = {
        "user_id": user.id,
        "level_code": level.code,
        "mode": mode,
        "qids": qids,
        "index": 0,
        "hp": hp,
        "max_hp": hp,
        "correct": 0,
        "wrong": 0,
        "difficulty": level.difficulty,
        "coins": 0,
        "exp": 0,
        "started": time.time(),
        "wrong_details": [],
        "answered": set(),
        "level_failed": False,
    }
    return {"run_id": run_id, "level_code": level.code, "total": len(qids),
            "hp": hp, "mode": mode}


def _pick_questions(db: Session, level: Level, mode: str, wrong_ids: list[int]) -> list[int]:
    tags = level.tags or []
    diff = level.difficulty
    if mode == "wrong_review":
        pool = [q for q in (db.get(Question, wid) for wid in wrong_ids) if q is not None]
        random.shuffle(pool)
        return [q.id for q in pool[:10]]
    # 主池：同关卡 tag 或学科 + 难度 ±1
    pool = db.query(Question).filter(Question.source == "seed").all()
    matched = [q for q in pool if (q.subject == level.subject or (tags and set(q.tags or []) & set(tags)))
               and abs(q.difficulty - diff) <= 1]
    fallback = [q for q in pool if q.type in ("choice", "blank")]
    chosen = matched if len(matched) >= 10 else matched + random.sample(
        [q for q in fallback if q not in matched], min(10 - len(matched), len(fallback)))
    if len(chosen) < 10:
        chosen = chosen + random.sample([q for q in fallback if q not in chosen],
                                        min(10 - len(chosen), len(fallback)))
    random.shuffle(chosen)
    return [q.id for q in chosen[:10]]


def current_question(db: Session, run_id: str) -> dict | None:
    run = RUNS.get(run_id)
    if not run:
        return None
    if run["index"] >= len(run["qids"]):
        return None
    q = db.get(Question, run["qids"][run["index"]])
    if q is None:
        return None
    return {
        "question_id": q.id,
        "type": q.type,
        "stem": q.stem,
        "options": q.options or [],
        "difficulty": q.difficulty,
        "subject": q.subject,
        "index": run["index"] + 1,
        "is_code": q.type == "code",
        "starter_code": (q.answer or {}).get("starter_code", "") if q.type == "code" else "",
    }


def answer_question(db: Session, user: User, run_id: str, question_id: int,
                    answer: Any) -> dict:
    run = RUNS.get(run_id)
    if not run or run["user_id"] != user.id:
        raise ValueError("闯关会话不存在或已失效")
    if run["level_failed"]:
        raise ValueError("生命值已耗尽，请复活或重开")
    q = db.get(Question, question_id)
    if q is None or question_id != run["qids"][run["index"]]:
        raise ValueError("题目状态异常")

    correct, expected = _grade(q, answer)
    char = user.character
    run["index"] += 1

    exp_gained = coins_gained = 0
    if correct:
        run["correct"] += 1
        exp_gained = 8 + q.difficulty * 4
        coins_gained = 1 + q.difficulty * 2
        char.total_correct += 1
    else:
        run["wrong"] += 1
        run["hp"] -= 1
        exp_gained = 2
        coins_gained = 1
        char.total_wrong += 1
        reason = _classify_wrong(q, answer)
        db.add(WrongAnswer(user_id=user.id, question_id=q.id,
                           user_answer=_fmt(answer), reason=reason))
        run["wrong_details"].append({"question_id": q.id, "reason": reason})
        if run["hp"] <= 0:
            run["level_failed"] = True

    run["exp"] += exp_gained
    run["coins"] += coins_gained
    run["answered"].add(q.id)

    growth.add_exp(db, char, exp_gained)
    growth.add_coins(db, char, coins_gained)
    growth.report_daily_event(db, user, "quest_questions")
    db.commit()
    growth.rebuild_leaderboard(db, user)

    finished = run["index"] >= len(run["qids"])
    return {
        "correct": correct,
        "explanation": q.explanation or "暂无解析",
        "knowledge_point": q.knowledge_point,
        "user_answer": answer,
        "expected_answer": expected,
        "ai_analysis": "",
        "hp_left": run["hp"],
        "coins_gained": coins_gained,
        "exp_gained": exp_gained,
        "difficulty_now": run["difficulty"],
        "finished": finished,
        "level_failed": run["level_failed"],
    }


def settle(db: Session, user: User, run_id: str, with_ai_analysis: bool = False) -> dict:
    """结算闯关：发放奖励、标记通关、解锁下一关、检查成就。"""
    run = RUNS.get(run_id)
    if not run or run["user_id"] != user.id:
        raise ValueError("闯关会话不存在或已失效")
    char = user.character
    total = len(run["qids"])
    correct, wrong = run["correct"], run["wrong"]
    accuracy = round(correct / total * 100, 1) if total else 0

    level = db.query(Level).filter(Level.code == run["level_code"]).first()
    progress = db.query(UserLevelProgress).filter(
        UserLevelProgress.user_id == user.id,
        UserLevelProgress.level_code == run["level_code"]).first()
    if progress is None:
        progress = UserLevelProgress(user_id=user.id, level_code=run["level_code"])
        db.add(progress)
    progress.attempts += 1

    completed = not run["level_failed"] and correct >= total * 0.6
    bonus_exp = bonus_coins = 0
    unlocked_next = None
    if completed:
        progress.status = "completed"
        progress.best_score = max(progress.best_score, correct)
        progress.completed_at = datetime.now()
        bonus_exp = level.base_exp if level else 50
        bonus_coins = level.base_coins if level else 20
        if accuracy == 100:
            bonus_exp += 30
            bonus_coins += 10
        char.total_quests += 1
        growth.report_daily_event(db, user, "quest_pass")
        growth.unlock_levels(db, user)
        newly = db.query(UserLevelProgress).filter(
            UserLevelProgress.user_id == user.id,
            UserLevelProgress.status == "unlocked").order_by(
            UserLevelProgress.id.desc()).first()
        if newly and newly.level_code != run["level_code"]:
            unlocked_next = newly.level_code
    else:
        progress.status = "unlocked"

    growth.add_exp(db, char, bonus_exp)
    growth.add_coins(db, char, bonus_coins)
    run["exp"] += bonus_exp
    run["coins"] += bonus_coins
    db.commit()

    new_ach = growth.check_achievements(db, user)
    growth.rebuild_leaderboard(db, user)

    # 错题本加 AI 解析（异步补充）
    return {
        "run_id": run_id,
        "level_code": run["level_code"],
        "correct_count": correct,
        "wrong_count": wrong,
        "accuracy": accuracy,
        "total_exp": run["exp"],
        "total_coins": run["coins"],
        "level_completed": completed,
        "unlocked_next": unlocked_next,
        "new_achievements": [_ach_dict(a) for a in new_ach],
        "score": correct,
    }


def revive(db: Session, user: User, run_id: str) -> dict:
    """代码币复活：20 币换 3 条命。"""
    run = RUNS.get(run_id)
    if not run or run["user_id"] != user.id:
        raise ValueError("闯关会话不存在")
    char = user.character
    if char.coins < 20:
        raise ValueError("代码币不足，完成每日任务可获取")
    char.coins -= 20
    run["hp"] = run["max_hp"]
    run["level_failed"] = False
    db.commit()
    return {"ok": True, "hp": run["hp"], "coins": char.coins}


def _grade(q: Question, answer: Any) -> tuple[bool, Any]:
    ans = q.answer or {}
    if q.type == "choice":
        return answer == ans.get("correct_index"), ans.get("correct_index")
    if q.type == "blank":
        expected = str(ans.get("answer", "")).strip().lower()
        got = str(answer or "").strip().lower()
        return got == expected, ans.get("answer")
    if q.type == "code":
        # 代码题在闯关中按「与参考答案关键行相似度」粗判（正式评测走 Bug 猎人）
        expected = str(ans.get("answer", ""))
        got = str(answer or "")
        return _code_similarity(expected, got) >= 0.6, "参考实现见解析"
    # short：关键词命中 60% 即判对
    kws = [k.lower() for k in (ans.get("keywords") or [])]
    got = str(answer or "").lower()
    hit = sum(1 for k in kws if k and k in got)
    rate = hit / len(kws) if kws else 0
    return rate >= 0.6, ans.get("answer", "")


def _code_similarity(expected: str, got: str) -> float:
    if not expected or not got:
        return 0.0
    exp_lines = {l.strip() for l in expected.splitlines() if l.strip() and not l.strip().startswith("#")}
    got_lines = {l.strip() for l in got.splitlines() if l.strip() and not l.strip().startswith("#")}
    if not exp_lines:
        return 0.0
    return len(exp_lines & got_lines) / len(exp_lines)


def _classify_wrong(q: Question, answer: Any) -> str:
    if q.type == "blank":
        return "计算错误"
    if q.type == "code":
        return "思路偏差"
    return "概念不清"


def _fmt(answer: Any) -> str:
    if isinstance(answer, (list, dict)):
        import json
        return json.dumps(answer, ensure_ascii=False)
    return str(answer)


def _ach_dict(a) -> dict:
    return {"code": a.code, "name": a.name, "icon": a.icon,
            "description": a.description, "exp_reward": a.exp_reward,
            "coin_reward": a.coin_reward}
