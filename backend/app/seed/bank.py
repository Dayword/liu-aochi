"""扩充题库：从 question_bank.json 载入单选题（幂等，按题干去重）。"""
import json
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import Question

BANK_PATH = Path(__file__).with_name("question_bank.json")


def seed_bank(db: Session) -> int:
    if not BANK_PATH.exists():
        return 0
    try:
        items = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    except Exception:
        return 0
    existing = {stem for (stem,) in db.query(Question.stem).all()}
    added = 0
    for it in items:
        stem = str(it.get("stem") or "").strip()
        options = [str(o).strip() for o in (it.get("options") or []) if str(o).strip()]
        index = it.get("correct_index")
        if (not stem or stem in existing or len(options) < 2
                or not isinstance(index, int) or not 0 <= index < len(options)):
            continue
        db.add(Question(
            type="choice",
            subject=str(it.get("subject") or "软件工程"),
            tags=list(it.get("tags") or []),
            difficulty=int(it.get("difficulty") or 2),
            stem=stem,
            options=options,
            answer={"correct_index": index},
            explanation=str(it.get("explanation") or ""),
            knowledge_point=str(it.get("knowledge_point") or ""),
            source="ai-bank",
        ))
        existing.add(stem)
        added += 1
    db.commit()
    return added
