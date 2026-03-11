# Telegram Ideas Bot

Bot de Telegram + tablero Kanban simple para capturar y gestionar ideas.

Importante: recibir mensajes del bot y abrir el Kanban desde fuera son cosas distintas.

- `polling`: no requiere URL publica para el bot, pero el Kanban solo se ve en local.
- `webhook`: requiere URL publica; asi puedes abrir Kanban desde fuera y Telegram entrega updates ahi.

## Stack

- FastAPI
- SQLite (SQLAlchemy)
- Jinja2 + HTMX

## Ejecutar local

Instalacion asistida (recomendado):

```bash
install.bat
```

Ese instalador:

- crea `venv` si falta
- instala dependencias
- instala `ngrok` (via winget) si falta
- te pide `TELEGRAM_BOT_TOKEN`
- genera/configura `.env`
- te permite guardar `ngrok authtoken`

1. Crea y activa un entorno virtual.
2. Instala dependencias:

```bash
pip install -r requirements.txt
```

3. Configura variables:

```bash
copy .env.example .env
```

Modo recomendado (plug and play sin ngrok):

- `TELEGRAM_MODE=polling`
- solo necesitas `TELEGRAM_BOT_TOKEN`

4. Arranca la app:

```bash
uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000`.

Con `TELEGRAM_MODE=polling`, el bot recibe mensajes sin webhook ni URL publica.

## Webhook plug and play con ngrok

Si quieres que todo inicie en un solo comando (app + ngrok + setWebhook automatico):

1. En `.env` define:

```env
TELEGRAM_BOT_TOKEN=tu_token
TELEGRAM_WEBHOOK_SECRET=tu_secret
```

2. Ejecuta:

```bash
python run_webhook.py
```

Opcional en Windows: doble click en `start_webhook.bat`.

El script:

- arranca `uvicorn`
- arranca `ngrok http 8000`
- detecta la URL publica de ngrok
- registra `setWebhook` automaticamente
- imprime la URL publica para abrir el Kanban

## Modo webhook (opcional)

Solo si quieres recibir mensajes en un servidor publico.

Define en `.env`:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_MODE=webhook`
- `TELEGRAM_WEBHOOK_SECRET`

Luego registra tu webhook (usa URL publica HTTPS):

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://TU_DOMINIO/telegram/webhook/<TELEGRAM_WEBHOOK_SECRET>"
```

## Comandos del bot

- `/start`
- `/idea <texto>`
- `/list`
- `/done <id>`
- Texto libre: crea idea en `inbox`
