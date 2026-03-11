from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Idea
from .schemas import IdeaCreate, IdeaUpdate, VALID_PRIORITIES, VALID_STATUSES


def _sanitize_status(status: str) -> str:
    return status if status in VALID_STATUSES else "inbox"


def _sanitize_priority(priority: str) -> str:
    return priority if priority in VALID_PRIORITIES else "med"


def create_idea(db: Session, payload: IdeaCreate) -> Idea:
    idea = Idea(
        title=payload.title.strip(),
        description=payload.description,
        status=_sanitize_status(payload.status),
        priority=_sanitize_priority(payload.priority),
        source=payload.source,
        telegram_user_id=payload.telegram_user_id,
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def list_ideas(db: Session, limit: int = 100) -> list[Idea]:
    stmt = select(Idea).order_by(Idea.created_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())


def list_ideas_by_status(db: Session) -> dict[str, list[Idea]]:
    ideas = list_ideas(db, limit=500)
    grouped = {"inbox": [], "todo": [], "doing": [], "done": []}
    for idea in ideas:
        grouped.setdefault(idea.status, []).append(idea)
    return grouped


def get_idea(db: Session, idea_id: int) -> Idea | None:
    return db.get(Idea, idea_id)


def update_idea(db: Session, idea: Idea, payload: IdeaUpdate) -> Idea:
    if payload.title is not None:
        idea.title = payload.title.strip()
    if payload.description is not None:
        idea.description = payload.description
    if payload.status is not None:
        idea.status = _sanitize_status(payload.status)
    if payload.priority is not None:
        idea.priority = _sanitize_priority(payload.priority)
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def set_idea_status(db: Session, idea: Idea, status: str) -> Idea:
    idea.status = _sanitize_status(status)
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def delete_idea(db: Session, idea: Idea) -> None:
    db.delete(idea)
    db.commit()
