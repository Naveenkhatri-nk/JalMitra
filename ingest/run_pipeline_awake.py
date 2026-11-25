"""
Run ingest/run_pipeline.py while keeping Windows from idle-sleeping, for the length of the run only.

Uses SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED); no power settings are changed,
and the flag is cleared on exit (it is also released automatically when this process ends).
Manual sleep, lid close or shutdown still work. Output goes to this process's stdout/stderr.

Usage:  python ingest/run_pipeline_awake.py
"""
import ctypes
import subprocess
import sys
from pathlib import Path

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    k32 = ctypes.windll.kernel32
    k32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    print("keep-awake: on", flush=True)
    try:
        code = subprocess.run([sys.executable, "-u", str(HERE / "run_pipeline.py")], cwd=ROOT).returncode
    finally:
        k32.SetThreadExecutionState(ES_CONTINUOUS)
        print("keep-awake: off", flush=True)
    sys.exit(code)


if __name__ == "__main__":
    main()
