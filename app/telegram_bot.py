import os

import httpx
from sqlalchemy.orm import Session

from . import crud
from .schemas import IdeaCreate


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def _api_base() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    return f"https://api.telegram.org/bot{token}"


async def send_message(chat_id: int, text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    if not token:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=20) as client:
        await client.post(url, json={"chat_id": chat_id, "text": text})


async def delete_webhook(drop_pending_updates: bool = False) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    if not token:
        return
    async with httpx.AsyncClient(timeout=20) as client:
        await client.get(
            f"{_api_base()}/deleteWebhook",
            params={"drop_pending_updates": str(drop_pending_updates).lower()},
        )


async def get_updates(offset: int | None = None, timeout: int = 25) -> list[dict]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", BOT_TOKEN)
    if not token:
        return []
    params: dict[str, object] = {
        "timeout": timeout,
        "allowed_updates": ["message", "edited_message"],
    }
    if offset is not None:
        params["offset"] = offset
    async with httpx.AsyncClient(timeout=timeout + 10) as client:
        response = await client.get(f"{_api_base()}/getUpdates", params=params)
    data = response.json()
    if not data.get("ok"):
        return []
    return data.get("result", [])


async def handle_update(update: dict, db: Session) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat = message.get("chat", {})
    from_user = message.get("from", {})
    chat_id = chat.get("id")
    telegram_user_id = from_user.get("id")
    text = (message.get("text") or "").strip()
    if not chat_id or not text:
        return

    if text.startswith("/start"):
        await send_message(
            chat_id,
            "Listo. Manda una idea con /idea <texto> o escribe texto libre y la guardo en inbox.",
        )
        return

    if text.startswith("/idea"):
        content = text.replace("/idea", "", 1).strip()
        if not content:
            await send_message(chat_id, "Uso: /idea texto de la idea")
            return
        idea = crud.create_idea(
            db,
            IdeaCreate(
                title=content,
                source="telegram",
                status="inbox",
                telegram_user_id=telegram_user_id,
            ),
        )
        await send_message(chat_id, f"Idea #{idea.id} guardada en inbox.")
        return

    if text.startswith("/list"):
        ideas = crud.list_ideas(db, limit=10)
        if not ideas:
            await send_message(chat_id, "No hay ideas todavia.")
            return
        lines = [f"#{i.id} [{i.status}] {i.title}" for i in ideas]
        await send_message(chat_id, "Ultimas ideas:\n" + "\n".join(lines))
        return

    if text.startswith("/done"):
        raw_id = text.replace("/done", "", 1).strip()
        if not raw_id.isdigit():
            await send_message(chat_id, "Uso: /done <id>")
            return
        idea = crud.get_idea(db, int(raw_id))
        if not idea:
            await send_message(chat_id, "No encontre esa idea.")
            return
        crud.set_idea_status(db, idea, "done")
        await send_message(chat_id, f"Idea #{idea.id} marcada como done.")
        return

    idea = crud.create_idea(
        db,
        IdeaCreate(
            title=text,
            source="telegram",
            status="inbox",
            telegram_user_id=telegram_user_id,
        ),
    )
    await send_message(chat_id, f"Guardada como idea #{idea.id}.")
