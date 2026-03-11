@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ============================================
echo   Telegram Ideas Bot - One-click installer
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python no esta instalado o no esta en PATH.
  echo Instala Python 3.11+ desde https://www.python.org/downloads/
  echo Durante la instalacion marca "Add python.exe to PATH".
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  echo [1/6] Creando entorno virtual...
  python -m venv venv
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
  )
) else (
  echo [1/6] Entorno virtual ya existe. OK
)

set "VENV_PY=venv\Scripts\python.exe"

echo [2/6] Actualizando pip...
"%VENV_PY%" -m pip install --upgrade pip

echo [3/6] Instalando dependencias...
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Fallo la instalacion de dependencias.
  pause
  exit /b 1
)

set "NGROK_BIN="
for /f "delims=" %%I in ('where ngrok 2^>nul') do (
  if not defined NGROK_BIN set "NGROK_BIN=%%I"
)

if not defined NGROK_BIN (
  echo [4/6] ngrok no encontrado. Intentando instalar con winget...
  where winget >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] winget no esta disponible para instalar ngrok automaticamente.
    echo Instala ngrok manualmente desde https://ngrok.com/download
    pause
    exit /b 1
  )

  winget install -e --id ngrok.ngrok --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (
    echo [ERROR] No se pudo instalar ngrok con winget.
    echo Prueba instalarlo manualmente desde https://ngrok.com/download
    pause
    exit /b 1
  )

  for /f "delims=" %%I in ('where ngrok 2^>nul') do (
    if not defined NGROK_BIN set "NGROK_BIN=%%I"
  )
)

if not defined NGROK_BIN (
  if exist "%ProgramFiles%\ngrok\ngrok.exe" set "NGROK_BIN=%ProgramFiles%\ngrok\ngrok.exe"
)
if not defined NGROK_BIN (
  if exist "%LocalAppData%\ngrok\ngrok.exe" set "NGROK_BIN=%LocalAppData%\ngrok\ngrok.exe"
)

if not defined NGROK_BIN (
  echo [ERROR] No pude localizar ngrok.exe en tu sistema.
  echo Instala ngrok y vuelve a ejecutar este instalador.
  pause
  exit /b 1
)

echo [5/6] Configuracion de .env
set "OVERWRITE=Y"
if exist ".env" (
  set /p OVERWRITE=Ya existe .env. Reescribirlo? [Y/n]: 
)

if /I not "%OVERWRITE%"=="N" (
  set "TELEGRAM_BOT_TOKEN="
  set /p TELEGRAM_BOT_TOKEN=Pegue su TELEGRAM_BOT_TOKEN: 
  if "%TELEGRAM_BOT_TOKEN%"=="" (
    echo [ERROR] El TELEGRAM_BOT_TOKEN no puede estar vacio.
    pause
    exit /b 1
  )

  set "TELEGRAM_WEBHOOK_SECRET="
  set /p TELEGRAM_WEBHOOK_SECRET=Webhook secret (Enter = auto): 
  if "%TELEGRAM_WEBHOOK_SECRET%"=="" (
    for /f "delims=" %%S in ('powershell -NoProfile -Command "'wk_' + [guid]::NewGuid().ToString('N')"') do set "TELEGRAM_WEBHOOK_SECRET=%%S"
  )

  > ".env" (
    echo TELEGRAM_BOT_TOKEN=%TELEGRAM_BOT_TOKEN%
    echo TELEGRAM_MODE=webhook
    echo TELEGRAM_WEBHOOK_SECRET=%TELEGRAM_WEBHOOK_SECRET%
    echo NGROK_BIN=%NGROK_BIN%
  )
) else (
  echo .env existente conservado.
)

echo.
echo [6/6] Configurar authtoken de ngrok
echo Crea cuenta/login en: https://dashboard.ngrok.com/get-started/your-authtoken
set "NGROK_AUTH_TOKEN="
set /p NGROK_AUTH_TOKEN=Pegue su ngrok authtoken (Enter = omitir): 
if not "%NGROK_AUTH_TOKEN%"=="" (
  "%NGROK_BIN%" config add-authtoken "%NGROK_AUTH_TOKEN%"
  if errorlevel 1 (
    echo [WARN] No se pudo guardar el authtoken.
    echo Hazlo manual: ngrok config add-authtoken TU_TOKEN
  )
) else (
  echo Omitido. Luego ejecuta manualmente:
  echo ngrok config add-authtoken TU_TOKEN
)

echo.
echo ============================================
echo Instalacion completa.
echo Para iniciar todo automatico, ejecuta:
echo start_webhook.bat
echo ============================================
echo.
pause
exit /b 0
