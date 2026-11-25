"""
eval/measure_ollama.py - hardware measurements for a local Ollama model (JalMitra 4.0 Phase 2).

Measures with num_ctx=4096: VRAM idle vs loaded (nvidia-smi), `ollama ps` (GPU/CPU split), RAM of the
ollama processes, cold-load time, prompt and generation tokens/sec (from eval_count/eval_duration),
whether "think": false really switches thinking off, and thinking-on latency for 3 questions.

Usage: python eval/measure_ollama.py --model qwen3:4b      -> eval/hardware_<model>_<date>.md
"""

import argparse
import csv
import datetime as dt
import io
import json
import re
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import llm_provider as lp  # noqa: E402

QUESTIONS = ["Is groundwater in Jodhpur district safe?", "फागी ब्लॉक की हालत बताइए",
             "Ajnala block ka recharge figure kya hai?", "ਲੁਧਿਆਣਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਪਾਣੀ ਦੀ ਸਥਿਤੀ ਕੀ ਹੈ?",
             "दौंड तालुका सुरक्षित आहे का?"]
SYS = "Describe the user's groundwater question as JSON with keys language, intent, places. Never write numbers."
SCHEMA = {"type": "object", "properties": {"language": {"type": "string"}, "intent": {"type": "string"},
                                           "places": {"type": "array", "items": {"type": "string"}}},
          "required": ["language", "intent", "places"]}


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding="utf-8",
                              errors="replace").stdout.strip()
    except Exception as e:
        return f"(failed: {e})"


def vram():
    out = run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv"])
    return out.splitlines()[-1] if out else "?"


def ollama_ram_mb():
    out = run(["tasklist", "/FO", "CSV", "/NH"])
    total, procs = 0, []
    for row in csv.reader(io.StringIO(out)):
        if row and row[0].lower().startswith(("ollama", "llama-server")):   # the model runs in llama-server.exe
            mb = int(re.sub(r"[^\d]", "", row[4]) or 0) / 1024
            procs.append(f"{row[0]} pid {row[1]}: {mb:.0f} MB")
            total += mb
    return total, procs


def unload(url, model):
    body = json.dumps({"model": model, "keep_alive": 0}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url + "/api/generate", data=body, method="POST",
                                                      headers={"Content-Type": "application/json"}), timeout=60).read()
    except Exception as e:
        return str(e)
    time.sleep(3)
    return "ok"


def tps(count, ms):
    return round(count / (ms / 1000), 1) if count and ms else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3:4b")
    ap.add_argument("--url", default=lp.DEFAULT_OLLAMA_URL)
    a = ap.parse_args()
    llm = lp.LLMProvider("ollama", model=a.model, ollama_url=a.url, timeout=300)
    L = [f"# Hardware measurements: {a.model} ({dt.datetime.now():%Y-%m-%d %H:%M})", "",
         "num_ctx 4096, temperature 0, think false unless stated. Measured by eval/measure_ollama.py.", ""]
    L += ["## Versions", "", "```", run(["ollama", "--version"]), run(["nvidia-smi", "--query-gpu=name,driver_version",
                                                                         "--format=csv,noheader"]), "```", ""]

    unload(a.url, a.model)
    idle = vram()
    ram0, _ = ollama_ram_mb()
    msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": QUESTIONS[0]}]
    cold = llm.chat(msgs, json_schema=SCHEMA, max_tokens=200)
    loaded = vram()
    ps = run(["ollama", "ps"])
    ram1, procs = ollama_ram_mb()
    L += ["## Memory", "", f"- VRAM idle (model unloaded): {idle}", f"- VRAM with model loaded: {loaded}",
          f"- ollama process RAM: {ram0:.0f} MB idle -> {ram1:.0f} MB loaded", ""] + \
         [f"  - {p}" for p in procs] + ["", "`ollama ps`:", "", "```", ps, "```", ""]
    L += ["## Cold load", "", f"- first request: total {cold.latency_ms:.0f} ms, load_duration "
          f"{cold.meta.get('load_duration_ms')} ms, ok={cold.ok} {cold.error or ''}", ""]

    rows = []
    for think in (False, True):
        for q in QUESTIONS if not think else QUESTIONS[:3]:
            r = llm.chat([{"role": "system", "content": SYS}, {"role": "user", "content": q}],
                         json_schema=SCHEMA, max_tokens=200 if not think else 2048, think=think)
            m = r.meta
            rows.append({"think": think, "q": q, "ok": r.ok, "ms": r.latency_ms,
                         "prompt_tok": r.tokens.get("prompt"), "gen_tok": r.tokens.get("completion"),
                         "prompt_tps": tps(r.tokens.get("prompt"), m.get("prompt_eval_duration_ms")),
                         "gen_tps": tps(r.tokens.get("completion"), m.get("eval_duration_ms")),
                         "thinking_chars": m.get("thinking_chars", 0), "think_tag": "<think>" in r.text,
                         "err": r.error or ""})
    L += ["## Speed (warm model)", "", "| think | question | ok | latency ms | prompt tok | gen tok | prompt tok/s | "
          "gen tok/s | thinking chars |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {'on' if r['think'] else 'off'} | {r['q']} | {r['ok']} | {r['ms']:.0f} | {r['prompt_tok']} | "
                 f"{r['gen_tok']} | {r['prompt_tps']} | {r['gen_tps']} | {r['thinking_chars']} |")
    off = [r for r in rows if not r["think"]]
    on = [r for r in rows if r["think"]]
    off_ok = all(r["thinking_chars"] == 0 and not r["think_tag"] for r in off)
    L += ["", f"- think=false: no thinking returned in {sum(1 for r in off if r['thinking_chars'] == 0)}/{len(off)} "
              f"answers -> {'works' if off_ok else 'DOES NOT fully work'}",
          f"- median latency think off: {statistics.median(r['ms'] for r in off):.0f} ms; think on (3 questions): "
          f"{statistics.median(r['ms'] for r in on):.0f} ms",
          f"- median generation speed: {statistics.median(r['gen_tps'] for r in rows if r['gen_tps']):.1f} tok/s", ""]
    out = HERE / f"hardware_{re.sub(r'[^A-Za-z0-9._-]', '-', a.model)}_{dt.date.today().isoformat()}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
