@echo off
REM ==========================================================================================
REM  STOP_JALMITRA.bat - stops the JalMitra web app (port 8501) and frees the AI model from the GPU.
REM  Ollama itself keeps running (other programs may use it); quit it from its tray icon if you want.
REM ==========================================================================================
setlocal
cd /d "%~dp0"
if "%JALMITRA_LLM_MODEL%"=="" set "JALMITRA_LLM_MODEL=qwen3:4b-instruct-2507-q4_K_M"
if "%JALMITRA_PORT%"=="" set "JALMITRA_PORT=8501"
echo Stopping JalMitra ...
powershell -NoProfile -Command ^
  "$p = Get-NetTCPConnection -LocalPort $env:JALMITRA_PORT -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique;" ^
  "if ($p) { foreach ($id in $p) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue; Write-Host ('[ok] stopped JalMitra (process ' + $id + ')') } } else { Write-Host '[ok] JalMitra was not running' };" ^
  "try { $b = @{model=$env:JALMITRA_LLM_MODEL; keep_alive=0} | ConvertTo-Json; Invoke-RestMethod -Uri http://127.0.0.1:11434/api/generate -Method Post -Body $b -ContentType 'application/json' -TimeoutSec 20 | Out-Null; Write-Host '[ok] AI model unloaded from the GPU' } catch { Write-Host '[ok] Ollama not running (nothing to unload)' }"
echo Done.
ping -n 3 127.0.0.1 1>nul
