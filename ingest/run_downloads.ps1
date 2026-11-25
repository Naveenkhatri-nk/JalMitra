# ingest/run_downloads.ps1 - run the JalMitra 4.0 long downloads sequentially.
# Launch detached with:
#   Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','E:\JalMitra\ingest\run_downloads.ps1'
# Each step's stdout/stderr goes to data\monitoring\logs\<name>.out / .err; a step failing does not stop the next.
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$py = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { $py = 'py'; $pre = @('-3') } else { $pre = @() }
$logs = Join-Path $root 'data\monitoring\logs'
New-Item -ItemType Directory -Force $logs | Out-Null
$runlog = Join-Path $logs 'run_downloads.log'

$steps = @(
    @{ name = 'cgwb_publications'; args = @('ingest\download_cgwb_publications.py') },
    @{ name = 'wris_rajasthan';    args = @('ingest\download_indiawris_gwl.py', '--scope', 'rajasthan', '--workers', '4') },
    @{ name = 'wris_national';     args = @('ingest\download_indiawris_gwl.py', '--scope', 'national', '--workers', '4') }
)

Add-Content $runlog "$(Get-Date -Format o) runner started (pid $PID)"
foreach ($s in $steps) {
    $out = Join-Path $logs "$($s.name).out"
    $err = Join-Path $logs "$($s.name).err"
    foreach ($f in @($out, $err)) {   # keep logs from an earlier run: rename, never overwrite
        if ((Test-Path $f) -and (Get-Item $f).Length -gt 0) {
            Rename-Item $f "$f.$((Get-Item $f).LastWriteTime.ToString('yyyyMMdd_HHmmss'))"
        }
    }
    Add-Content $runlog "$(Get-Date -Format o) start $($s.name)"
    $p = Start-Process -FilePath $py -ArgumentList ($pre + @('-u') + $s.args) -WorkingDirectory $root `
        -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -Wait
    Add-Content $runlog "$(Get-Date -Format o) end $($s.name) exit=$($p.ExitCode)"
}
Add-Content $runlog "$(Get-Date -Format o) runner finished"
