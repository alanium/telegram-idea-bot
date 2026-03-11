from datetime import datetime

from pydantic import BaseModel, Field


VALID_STATUSES = {"inbox", "todo", "doing", "done"}
VALID_PRIORITIES = {"low", "med", "high"}


class IdeaBase(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str | None = None
    priority: str = "med"


class IdeaCreate(IdeaBase):
    status: str = "inbox"
    source: str = "web"
    telegram_user_id: int | None = None


class IdeaUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = None
    status: str | None = None
    priority: str | None = None


class IdeaStatusUpdate(BaseModel):
    status: str


class IdeaOut(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    priority: str
    source: str
    telegram_user_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
