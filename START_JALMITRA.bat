@echo off
REM ==========================================================================================
REM  START_JALMITRA.bat - starts JalMitra (local AI groundwater assistant) on THIS computer only.
REM  1. checks the Python environment (.venv)
REM  2. checks that Ollama is installed and running (starts it if needed)
REM  3. checks that the AI model and the document model are installed (no automatic downloads)
REM  4. loads the AI model into the GPU
REM  5. starts JalMitra on http://localhost:8501 (localhost only) and opens the browser
REM  Stop it with STOP_JALMITRA.bat (or close the "JalMitra server" window).
REM ==========================================================================================
setlocal EnableExtensions
cd /d "%~dp0"
title JalMitra - starting
if "%JALMITRA_LLM_MODEL%"=="" set "JALMITRA_LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M"
set "EMBED_MODEL=bge-m3"
set "PORT=8501"
if not "%JALMITRA_PORT%"=="" set "PORT=%JALMITRA_PORT%"
set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
set "OLLAMA_APP=%LOCALAPPDATA%\Programs\Ollama\ollama app.exe"

echo.
echo  JalMitra - Your Intelligent Groundwater Assistant
echo  -------------------------------------------------
echo  AI model : %JALMITRA_LLM_MODEL%
echo.

REM ---------------------------------------------------------------- 1. Python environment
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] The Python environment .venv was not found in %CD%.
    echo         Create it and install the packages first ^(see README.md^). Nothing was installed automatically.
    goto :fail
)
".venv\Scripts\python.exe" -c "import streamlit, chromadb" 1>nul 2>nul
if errorlevel 1 (
    echo [ERROR] streamlit or chromadb is missing in .venv.
    echo         Install them with:  .venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-llm.txt
    goto :fail
)
echo [ok] Python environment

REM ---------------------------------------------------------------- 2. Ollama installed and running
if not exist "%OLLAMA_EXE%" (
    where ollama 1>nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Ollama is not installed. Install it from https://ollama.com/download ^(or: winget install Ollama.Ollama^)
        goto :fail
    )
    set "OLLAMA_EXE=ollama"
)
call :ollama_up
if errorlevel 1 (
    echo [..] Ollama is not running - starting it ...
    if exist "%OLLAMA_APP%" (
        start "" "%OLLAMA_APP%"
    ) else (
        start "Ollama" /min "%OLLAMA_EXE%" serve
    )
    for /l %%i in (1,1,30) do (
        call :ollama_up && goto :ollama_ok
        ping -n 2 127.0.0.1 1>nul
    )
    echo [ERROR] Ollama did not start within 30 seconds. Open the Ollama app from the Start menu and run this again.
    goto :fail
)
:ollama_ok
echo [ok] Ollama is running on http://localhost:11434

REM ---------------------------------------------------------------- 3. models installed (no downloads here)
"%OLLAMA_EXE%" list 2>nul | findstr /i /c:"%JALMITRA_LLM_MODEL%" 1>nul
if errorlevel 1 (
    echo [ERROR] The AI model %JALMITRA_LLM_MODEL% is not installed.
    echo         Install it once with:  "%OLLAMA_EXE%" pull %JALMITRA_LLM_MODEL%
    goto :fail
)
echo [ok] AI model %JALMITRA_LLM_MODEL%
"%OLLAMA_EXE%" list 2>nul | findstr /i /c:"%EMBED_MODEL%" 1>nul
if errorlevel 1 (
    echo [ERROR] The document search model %EMBED_MODEL% is not installed.
    echo         Install it once with:  "%OLLAMA_EXE%" pull %EMBED_MODEL%
    goto :fail
)
echo [ok] Document search model %EMBED_MODEL%

REM ---------------------------------------------------------------- 4. load the AI model into the GPU (keeps it 30 min)
echo [..] Loading the AI model into the GPU ^(first time can take up to a minute^) ...
powershell -NoProfile -Command "try { $b = @{model=$env:JALMITRA_LLM_MODEL; prompt=''; keep_alive='30m'} | ConvertTo-Json; Invoke-RestMethod -Uri http://127.0.0.1:11434/api/generate -Method Post -Body $b -ContentType 'application/json' -TimeoutSec 180 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo [warning] The model could not be pre-loaded; JalMitra will load it on the first question.
) else (
    echo [ok] AI model loaded
)

REM ---------------------------------------------------------------- 5. JalMitra (localhost only)
call :jalmitra_up
if not errorlevel 1 (
    echo [ok] JalMitra is already running.
    goto :open
)
echo [..] Starting JalMitra on http://localhost:%PORT% ^(this computer only^) ...
start "JalMitra server" /min ".venv\Scripts\python.exe" -m streamlit run app.py --server.address localhost --server.port %PORT% --server.headless true --browser.gatherUsageStats false
for /l %%i in (1,1,60) do (
    call :jalmitra_up && goto :open
    ping -n 2 127.0.0.1 1>nul
)
echo [ERROR] JalMitra did not start within 60 seconds. Look at the "JalMitra server" window for the error.
goto :fail

:open
echo [ok] JalMitra is at http://localhost:%PORT%
if not "%JALMITRA_NO_BROWSER%"=="1" start "" "http://localhost:%PORT%"
echo.
echo  JalMitra is running. Keep the "JalMitra server" window open while you use it.
echo  To stop it: run STOP_JALMITRA.bat
echo.
ping -n 4 127.0.0.1 1>nul
exit /b 0

:fail
echo.
echo  JalMitra was NOT started. Fix the problem above and run START_JALMITRA.bat again.
pause
exit /b 1

:ollama_up
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri http://127.0.0.1:11434/api/version -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }"
exit /b %errorlevel%

:jalmitra_up
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri http://127.0.0.1:%PORT%/_stcore/health -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }"
exit /b %errorlevel%
