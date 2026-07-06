@echo off
setlocal EnableDelayedExpansion
title Desktop Agent - Setup
color 0A

echo.
echo  =============================================
echo   Desktop Agent - Automated Setup
echo  =============================================
echo.

:: ── 1. Find Python ───────────────────────────────────────────────────────
set "PYTHON="

py --version >nul 2>&1
if not errorlevel 1 set "PYTHON=py"
if defined PYTHON goto :python_found

python --version >nul 2>&1
if not errorlevel 1 set "PYTHON=python"
if defined PYTHON goto :python_found

python3 --version >nul 2>&1
if not errorlevel 1 set "PYTHON=python3"
if defined PYTHON goto :python_found

if exist "venv\Scripts\python.exe" set "PYTHON=%~dp0venv\Scripts\python.exe"
if defined PYTHON goto :python_found

for %%P in (
    "%LocalAppData%\Programs\Python\Python314\python.exe"
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python314\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
) do (
    if exist %%P (
        set "PYTHON=%%~P"
        goto :python_found
    )
)

echo  [ERROR] Python not found. Install from https://python.org
echo          Check "Add python.exe to PATH" during install, then re-run.
echo.
pause & exit /b 1

:python_found
for /f "tokens=*" %%v in ('"%PYTHON%" --version 2^>^&1') do echo  [OK] %%v found

:: ── 2. Check / start Ollama ──────────────────────────────────────────────
echo.
where ollama >nul 2>&1
if errorlevel 1 (
    echo  [WARN] Ollama not installed. Get it from https://ollama.com/download
    echo         After installing, re-run setup to pull the model.
    goto :skip_ollama
)

echo  [OK] Ollama is installed.

curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo  [INFO] Starting Ollama server in background...
    start /B ollama serve
    timeout /t 4 /nobreak >nul
) else (
    echo  [OK] Ollama server is running.
)

ollama list 2>nul | findstr /I "qwen2.5:14b" >nul 2>&1
if not errorlevel 1 goto :model_ready

echo.
echo  [INFO] Downloading model qwen2.5:14b  (~8 GB, one-time download)
echo         This will take a while - go make some tea!
echo.
ollama pull qwen2.5:14b
if errorlevel 1 (
    echo  [WARN] Pull failed. Run later:  ollama pull qwen2.5:14b
) else (
    echo  [OK] Model ready.
)
goto :skip_ollama

:model_ready
echo  [OK] Model qwen2.5:14b already downloaded.

:skip_ollama

:: ── 3. Create virtual environment ────────────────────────────────────────
echo.
echo  [INFO] Setting up Python virtual environment...
if exist "venv\Scripts\python.exe" goto :venv_exists

"%PYTHON%" -m venv venv
if errorlevel 1 (
    echo  [ERROR] Failed to create virtual environment.
    pause & exit /b 1
)
echo  [OK] Virtual environment created.
goto :venv_done

:venv_exists
echo  [OK] Virtual environment already exists.

:venv_done

:: ── 4. Install packages ──────────────────────────────────────────────────
echo  [INFO] Installing packages (may take a few minutes)...
call venv\Scripts\activate.bat
venv\Scripts\python.exe -m pip install --upgrade pip -q
venv\Scripts\python.exe -m pip install "setuptools<70" -q
venv\Scripts\python.exe -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo  [ERROR] Package installation failed.
    pause & exit /b 1
)
echo  [OK] Packages installed.

:: ── 5. Create launcher ───────────────────────────────────────────────────
set "VENV_PYW=%~dp0venv\Scripts\pythonw.exe"
set "VENV_PY=%~dp0venv\Scripts\python.exe"
set "APP=%~dp0app.py"

(
    echo @echo off
    echo cd /d "%%~dp0"
    echo if exist "%VENV_PYW%" ^(
    echo     start "" "%VENV_PYW%" "%APP%"
    echo ^) else ^(
    echo     "%VENV_PY%" "%APP%"
    echo ^)
) > launch.bat
echo  [OK] launch.bat created.

:: ── 6. Desktop shortcut ──────────────────────────────────────────────────
set "LNK=%USERPROFILE%\Desktop\Desktop Agent.lnk"
set "LAUNCH=%~dp0launch.bat"

powershell -NoProfile -Command "$sh=New-Object -ComObject WScript.Shell; $sc=$sh.CreateShortcut('%LNK%'); $sc.TargetPath='%LAUNCH%'; $sc.WorkingDirectory='%~dp0'; $sc.IconLocation='%SystemRoot%\System32\shell32.dll,43'; $sc.WindowStyle=7; $sc.Save()" >nul 2>&1

if exist "%LNK%" (
    echo  [OK] "Desktop Agent" shortcut created on your Desktop.
) else (
    echo  [WARN] Could not create shortcut - use launch.bat directly.
)

:: ── Done ─────────────────────────────────────────────────────────────────
echo.
echo  =============================================
echo   All done!
echo   Double-click "Desktop Agent" on your Desktop
echo   - or - run launch.bat to start the app.
echo  =============================================
echo.
pause
