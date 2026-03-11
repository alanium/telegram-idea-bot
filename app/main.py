import os
import asyncio

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, telegram_bot
from .db import Base, SessionLocal, engine, get_db
from .schemas import IdeaCreate, IdeaStatusUpdate, IdeaUpdate


load_dotenv()


app = FastAPI(title="Telegram Ideas Bot")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
poller_task: asyncio.Task[None] | None = None


async def poll_telegram_updates() -> None:
    offset: int | None = None
    while True:
        try:
            updates = await telegram_bot.get_updates(offset=offset)
            for update in updates:
                update_id = update.get("update_id")
                if isinstance(update_id, int):
                    offset = update_id + 1
                db = SessionLocal()
                try:
                    await telegram_bot.handle_update(update, db)
                finally:
                    db.close()
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(2)


@app.on_event("startup")
async def on_startup() -> None:
    global poller_task
    Base.metadata.create_all(bind=engine)
    mode = os.getenv("TELEGRAM_MODE", "polling").strip().lower()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if mode == "polling" and token:
        await telegram_bot.delete_webhook(drop_pending_updates=False)
        poller_task = asyncio.create_task(poll_telegram_updates())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global poller_task
    if poller_task is not None:
        poller_task.cancel()
        try:
            await poller_task
        except asyncio.CancelledError:
            pass
        poller_task = None


@app.get("/", response_class=HTMLResponse)
def kanban(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    grouped = crud.list_ideas_by_status(db)
    context = {"request": request, "grouped": grouped, "statuses": ["inbox", "todo", "doing", "done"]}
    return templates.TemplateResponse("kanban.html", context)


@app.get("/ideas/{idea_id}", response_class=HTMLResponse)
def idea_detail(idea_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    idea = crud.get_idea(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    return templates.TemplateResponse("idea_detail.html", {"request": request, "idea": idea})


@app.post("/ideas", response_class=HTMLResponse)
def create_idea_web(
    request: Request,
    title: str = Form(...),
    description: str = Form(default=""),
    priority: str = Form(default="med"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    crud.create_idea(
        db,
        IdeaCreate(
            title=title,
            description=description or None,
            priority=priority,
            status="inbox",
            source="web",
        ),
    )
    grouped = crud.list_ideas_by_status(db)
    return templates.TemplateResponse("partials/board.html", {"request": request, "grouped": grouped})


@app.post("/ideas/{idea_id}/status", response_class=HTMLResponse)
def update_status_web(
    request: Request,
    idea_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    idea = crud.get_idea(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    crud.set_idea_status(db, idea, status)
    grouped = crud.list_ideas_by_status(db)
    return templates.TemplateResponse("partials/board.html", {"request": request, "grouped": grouped})


@app.post("/ideas/{idea_id}/edit")
def edit_idea_web(
    idea_id: int,
    title: str = Form(...),
    description: str = Form(default=""),
    priority: str = Form(default="med"),
    status: str = Form(default="inbox"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    idea = crud.get_idea(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    crud.update_idea(
        db,
        idea,
        IdeaUpdate(
            title=title,
            description=description or None,
            priority=priority,
            status=status,
        ),
    )
    return RedirectResponse(url=f"/ideas/{idea_id}", status_code=303)


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(secret: str, payload: dict, db: Session = Depends(get_db)) -> dict:
    mode = os.getenv("TELEGRAM_MODE", "polling").strip().lower()
    if mode != "webhook":
        raise HTTPException(status_code=409, detail="Webhook disabled in polling mode")
    expected = os.getenv("TELEGRAM_WEBHOOK_SECRET", "dev-secret")
    if secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")
    await telegram_bot.handle_update(payload, db)
    return {"ok": True}


@app.post("/api/ideas")
def create_idea_api(payload: IdeaCreate, db: Session = Depends(get_db)) -> dict:
    idea = crud.create_idea(db, payload)
    return {"id": idea.id}


@app.patch("/api/ideas/{idea_id}")
def update_idea_api(idea_id: int, payload: IdeaUpdate, db: Session = Depends(get_db)) -> dict:
    idea = crud.get_idea(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    updated = crud.update_idea(db, idea, payload)
    return {"id": updated.id, "status": updated.status}


@app.patch("/api/ideas/{idea_id}/status")
def update_status_api(idea_id: int, payload: IdeaStatusUpdate, db: Session = Depends(get_db)) -> dict:
    idea = crud.get_idea(db, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    updated = crud.set_idea_status(db, idea, payload.status)
    return {"id": updated.id, "status": updated.status}
