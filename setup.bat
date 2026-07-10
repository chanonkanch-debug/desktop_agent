@echo off
setlocal EnableDelayedExpansion
title Desktop Agent - Setup
color 0A

echo.
echo  =============================================
echo   Desktop Agent - Setup
echo  =============================================
echo.

:: ─────────────────────────────────────────────────────────────────────────────
:: 1. Find Python  (prefer 3.12 → 3.11 → 3.13, avoid 3.14+)
:: ─────────────────────────────────────────────────────────────────────────────
set "PY_CMD="
set "PY_VER="
set "PY_MAJ=0"
set "PY_MIN=0"

:: If we already have a local Python 3.12 from a previous setup, use it first
if exist "%~dp0python312\python.exe" (
    set "PY_CMD=%~dp0python312\python.exe"
    for /f "tokens=2" %%W in ('"%~dp0python312\python.exe" --version 2^>^&1') do set "PY_VER=%%W"
    echo  [OK] Using local Python 3.12 at python312\
    goto :parse_ver
)

:: Try py launcher for stable versions first
:: NOTE: "py -X.Y --version" can exit 0 even when that version isn't
:: installed (it just prints "[ERROR] No runtime installed..."), so the
:: output text is validated instead of trusting errorlevel alone.
for %%V in (3.12 3.11 3.13) do (
    if not defined PY_CMD (
        for /f "tokens=1,2" %%T in ('py -%%V --version 2^>^&1') do (
            if /i "%%T"=="Python" (
                echo %%U| findstr /r "^[0-9]" >nul
                if not errorlevel 1 (
                    set "PY_CMD=py -%%V"
                    set "PY_VER=%%U"
                )
            )
        )
    )
)

:: Fallback: bare py / python / python3
:: NOTE: on Windows, "python" with no real install runs the Microsoft
:: Store alias stub, which prints "Python was not found..." and also
:: exits 0 — same validation is needed here.
if not defined PY_CMD (
    for %%C in (py python python3) do (
        if not defined PY_CMD (
            for /f "tokens=1,2" %%T in ('%%C --version 2^>^&1') do (
                if /i "%%T"=="Python" (
                    echo %%U| findstr /r "^[0-9]" >nul
                    if not errorlevel 1 (
                        set "PY_CMD=%%C"
                        set "PY_VER=%%U"
                    )
                )
            )
        )
    )
)

:parse_ver
if not defined PY_VER goto :python_bad

for /f "tokens=1,2 delims=." %%A in ("%PY_VER%") do (
    set "PY_MAJ=%%A"
    set "PY_MIN=%%B"
)

:: Guard against a garbage/non-numeric version string reaching the EQU/LSS
:: comparisons below — a bad value there is a batch syntax error, not a
:: clean failure, and would silently kill the whole script.
set "VALID_VER=1"
if not defined PY_MAJ set "VALID_VER="
if not defined PY_MIN set "VALID_VER="
for /f "delims=0123456789" %%z in ("%PY_MAJ%%PY_MIN%") do set "VALID_VER="
if not defined VALID_VER (
    echo  [WARN] Could not parse Python version from "%PY_VER%".
    set "PY_CMD="
    goto :python_bad
)

:: Too old
if %PY_MAJ% EQU 3 if %PY_MIN% LSS 10 (
    echo  [WARN] Found Python %PY_VER% — too old (need 3.10+^).
    set "PY_CMD="
    goto :python_bad
)

:: Too new (3.14+) — some packages lack wheels
if %PY_MAJ% EQU 3 if %PY_MIN% GEQ 14 (
    echo  [WARN] Found Python %PY_VER% — too new. Some packages have no wheels yet.
    set "PY_CMD="
    goto :python_bad
)

echo  [OK] Python %PY_VER% found.
goto :python_ok

:python_bad
echo.
echo  ┌──────────────────────────────────────────────────────────────────────┐
echo  │  A compatible Python (3.10 – 3.13) was not found.                   │
echo  │                                                                      │
echo  │  This setup can download and install Python 3.12 for you.           │
echo  │  It installs into this project folder only — no admin rights,       │
echo  │  no changes to your system or PATH.                                  │
echo  └──────────────────────────────────────────────────────────────────────┘
echo.
set /p "DL_PY=   Download Python 3.12 now? (Y/N): "
if /i not "%DL_PY%"=="Y" (
    echo.
    echo  Manual install: https://www.python.org/downloads/release/python-3129/
    echo  Check "Add python.exe to PATH", then re-run this setup.
    echo.
    pause & exit /b 1
)

echo.
echo  [INFO] Downloading Python 3.12.9 installer (~25 MB)...
set "PY_INST=%TEMP%\python-3.12.9-amd64.exe"
curl -# -L -o "%PY_INST%" "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe"
if errorlevel 1 (
    echo  [ERROR] Download failed. Check your internet connection.
    pause & exit /b 1
)

echo  [INFO] Installing Python 3.12 into python312\ (no admin needed)...
"%PY_INST%" /quiet InstallAllUsers=0 PrependPath=0 "TargetDir=%~dp0python312"
if errorlevel 1 (
    echo  [ERROR] Python 3.12 installation failed.
    echo          Try installing manually from https://www.python.org/downloads/release/python-3129/
    pause & exit /b 1
)

set "PY_CMD=%~dp0python312\python.exe"
set "PY_VER=3.12.9"
echo  [OK] Python 3.12 installed into python312\

:python_ok

:: ─────────────────────────────────────────────────────────────────────────────
:: 2. Require Ollama
:: ─────────────────────────────────────────────────────────────────────────────
echo.
where ollama >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Ollama is not installed.
    echo.
    echo  Please install Ollama from:
    echo    https://ollama.com/download
    echo.
    echo  After installing Ollama, re-run this setup.
    echo.
    pause & exit /b 1
)
echo  [OK] Ollama is installed.

:: Start server if not already running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo  [INFO] Starting Ollama server...
    start /B ollama serve
    timeout /t 5 /nobreak >nul
) else (
    echo  [OK] Ollama server is running.
)

:: ─────────────────────────────────────────────────────────────────────────────
:: 3. Pick AI model
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo  ┌──────────────────────────────────────────────────────────────────────┐
echo  │                  Choose an AI model to download                      │
echo  │                                                                      │
echo  │  Larger models are smarter but need more RAM and disk space.         │
echo  │  Minimum RAM: 8 GB for 8b models, 16 GB for 14b models.             │
echo  └──────────────────────────────────────────────────────────────────────┘
echo.
echo    #   Model                Size    Notes
echo    -   ----------------     ------  ------------------------------------
echo    1   deepseek-r1:14b      9 GB    Best reasoning          [Recommended]
echo    2   deepseek-r1:8b       5 GB    Fast, needs less RAM
echo    3   deepseek-r1:1.5b     1 GB    Very fast, basic tasks only
echo    4   qwen2.5:14b          9 GB    Strong at coding tasks
echo    5   qwen2.5:7b           5 GB    Good at coding, lighter
echo    6   llama3.1:8b          5 GB    Fast general purpose
echo    7   Skip                         I already have a model pulled
echo.
set "MODEL_NAME="
set /p "MODEL_CHOICE=   Enter number (1-7) then press Enter: "
echo.

if "%MODEL_CHOICE%"=="1" set "MODEL_NAME=deepseek-r1:14b"
if "%MODEL_CHOICE%"=="2" set "MODEL_NAME=deepseek-r1:8b"
if "%MODEL_CHOICE%"=="3" set "MODEL_NAME=deepseek-r1:1.5b"
if "%MODEL_CHOICE%"=="4" set "MODEL_NAME=qwen2.5:14b"
if "%MODEL_CHOICE%"=="5" set "MODEL_NAME=qwen2.5:7b"
if "%MODEL_CHOICE%"=="6" set "MODEL_NAME=llama3.1:8b"
if "%MODEL_CHOICE%"=="7" goto :skip_model

if not defined MODEL_NAME (
    echo  [WARN] Unrecognised choice — skipping model download.
    goto :skip_model
)

:: Check if already downloaded
ollama list 2>nul | findstr /I "%MODEL_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo  [OK] %MODEL_NAME% is already downloaded.
    goto :model_done
)

echo  [INFO] Downloading %MODEL_NAME% — this may take a while.
echo         You can cancel with Ctrl+C and re-run setup later.
echo.
ollama pull %MODEL_NAME%
if errorlevel 1 (
    echo  [WARN] Download failed. Run later:  ollama pull %MODEL_NAME%
    goto :skip_model
)
echo  [OK] Model downloaded.

:model_done
:: Write chosen model into config.yaml
echo  [INFO] Updating config.yaml...
powershell -NoProfile -Command ^
  "(Get-Content 'config.yaml' -Raw) -replace '(?m)^model:.*', 'model: %MODEL_NAME%' | Set-Content 'config.yaml' -Encoding utf8" >nul 2>&1
echo  [OK] config.yaml set to model: %MODEL_NAME%

:skip_model

:: ─────────────────────────────────────────────────────────────────────────────
:: 4. Create virtual environment
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo  [INFO] Setting up Python virtual environment...

if exist "venv\Scripts\python.exe" (
    set "VENV_MAJ="
    set "VENV_MIN="
    for /f "tokens=2" %%W in ('venv\Scripts\python.exe --version 2^>^&1') do (
        for /f "tokens=1,2 delims=." %%A in ("%%W") do (
            set "VENV_MAJ=%%A"
            set "VENV_MIN=%%B"
        )
    )
    if "!VENV_MAJ!.!VENV_MIN!"=="%PY_MAJ%.%PY_MIN%" (
        echo  [OK] Virtual environment already exists ^(Python !VENV_MAJ!.!VENV_MIN!^).
        goto :venv_done
    )
    echo  [WARN] Existing venv uses Python !VENV_MAJ!.!VENV_MIN!, but %PY_MAJ%.%PY_MIN% is selected.
    echo  [INFO] Removing and recreating virtual environment...
    rmdir /s /q venv
)

%PY_CMD% -m venv venv
if errorlevel 1 (
    echo  [ERROR] Failed to create virtual environment.
    pause & exit /b 1
)
echo  [OK] Virtual environment created with Python %PY_VER%.

:venv_done

:: ─────────────────────────────────────────────────────────────────────────────
:: 5. Install packages
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo  [INFO] Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip -q

echo  [INFO] Installing setuptools (pinned for compatibility)...
venv\Scripts\python.exe -m pip install "setuptools<70" -q

:: tiktoken: --prefer-binary avoids Rust/MSVC source compilation
echo  [INFO] Installing tiktoken (you will see download progress)...
venv\Scripts\python.exe -m pip install tiktoken --prefer-binary
if errorlevel 1 (
    echo.
    echo  [ERROR] tiktoken failed to install.
    echo.
    echo  This means there is no pre-built wheel for Python %PY_VER%.
    echo  Delete the venv\ folder, then re-run setup and choose
    echo  to download Python 3.12 when prompted.
    echo.
    pause & exit /b 1
)
echo  [OK] tiktoken installed.

echo  [INFO] Installing remaining packages — this can take 5-15 minutes.
echo         You will see each package as it downloads. Do not close this window.
echo.
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo  [ERROR] Package installation failed. Check the errors above.
    pause & exit /b 1
)
echo  [OK] All packages installed.

:: ─────────────────────────────────────────────────────────────────────────────
:: 6. Create launcher
:: ─────────────────────────────────────────────────────────────────────────────
echo.
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

:: ─────────────────────────────────────────────────────────────────────────────
:: 7. Desktop shortcut
:: ─────────────────────────────────────────────────────────────────────────────
set "LNK=%USERPROFILE%\Desktop\Desktop Agent.lnk"
set "LAUNCH=%~dp0launch.bat"
set "ICON=%~dp0icon.ico"

powershell -NoProfile -Command ^
  "$sh=New-Object -ComObject WScript.Shell; $sc=$sh.CreateShortcut('%LNK%'); $sc.TargetPath='%LAUNCH%'; $sc.WorkingDirectory='%~dp0'; $sc.IconLocation='%ICON%'; $sc.WindowStyle=7; $sc.Save()" >nul 2>&1

if exist "%LNK%" (
    echo  [OK] Desktop shortcut created.
) else (
    echo  [WARN] Could not create shortcut — use launch.bat directly.
)

:: ─────────────────────────────────────────────────────────────────────────────
:: Done
:: ─────────────────────────────────────────────────────────────────────────────
echo.
echo  =============================================
echo   All done!
echo   Double-click "Desktop Agent" on your Desktop
echo   - or - run launch.bat to start the app.
echo  =============================================
echo.
pause
