import os
import signal
import subprocess
import sys
import time

import httpx
from dotenv import load_dotenv


def _wait_for_ngrok_url(timeout_seconds: int = 30) -> str:
    deadline = time.time() + timeout_seconds
    api_url = "http://127.0.0.1:4040/api/tunnels"
    while time.time() < deadline:
        try:
            response = httpx.get(api_url, timeout=2)
            data = response.json()
            for tunnel in data.get("tunnels", []):
                public_url = tunnel.get("public_url", "")
                if public_url.startswith("https://"):
                    return public_url
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("No pude obtener URL publica de ngrok en 30s")


def _set_webhook(token: str, webhook_url: str) -> None:
    endpoint = f"https://api.telegram.org/bot{token}/setWebhook"
    response = httpx.get(endpoint, params={"url": webhook_url}, timeout=15)
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Error setWebhook: {data}")


def main() -> int:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    ngrok_bin = os.getenv("NGROK_BIN", "ngrok").strip()
    app_port = os.getenv("APP_PORT", "8000").strip()

    if not token:
        print("Falta TELEGRAM_BOT_TOKEN en .env")
        return 1
    if not secret:
        print("Falta TELEGRAM_WEBHOOK_SECRET en .env")
        return 1

    uvicorn_env = os.environ.copy()
    uvicorn_env["TELEGRAM_MODE"] = "webhook"

    uvicorn_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", app_port]
    ngrok_cmd = [ngrok_bin, "http", app_port]

    uvicorn_proc = subprocess.Popen(uvicorn_cmd, env=uvicorn_env)
    ngrok_proc = subprocess.Popen(ngrok_cmd)

    try:
        public_base = _wait_for_ngrok_url()
        webhook_url = f"{public_base}/telegram/webhook/{secret}"
        _set_webhook(token, webhook_url)
        print(f"Kanban publico: {public_base}")
        print(f"Webhook activo: {webhook_url}")
        print("Presiona Ctrl+C para apagar app + ngrok")

        while True:
            if uvicorn_proc.poll() is not None:
                return uvicorn_proc.returncode or 0
            if ngrok_proc.poll() is not None:
                return ngrok_proc.returncode or 0
            time.sleep(1)
    except KeyboardInterrupt:
        return 0
    finally:
        for proc in (uvicorn_proc, ngrok_proc):
            if proc.poll() is None:
                if os.name == "nt":
                    proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    proc.terminate()
        time.sleep(1)
        for proc in (uvicorn_proc, ngrok_proc):
            if proc.poll() is None:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
