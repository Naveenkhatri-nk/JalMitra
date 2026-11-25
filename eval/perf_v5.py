"""
eval/perf_v5.py - performance benchmark (JalMitra 4.0 Phase 5). Real local models, no downloads.

Measures: cold model load (chat model qwen3:4b-instruct-2507-q4_K_M and embedding model bge-m3), time to first
token (streaming /api/chat, measurement only - the app never shows unverified text), full generation time and
tokens/s for short / medium / long prompts built exactly like llm_compose builds them, RAG retrieval time (cold,
warm, cached embedding), the full checked pipeline stage by stage (first run and cached run), rule-only answer
time, GPU memory (nvidia-smi) and RAM of the Ollama runners.

Usage: python eval/perf_v5.py   -> eval/perf_v5_<date>.md
"""

import csv
import datetime as dt
import io
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
for _k in [k for k in os.environ if k.startswith("JALMITRA_")]:
    del os.environ[_k]

import engine  # noqa: E402
import llm_compose  # noqa: E402
import llm_provider as lp  # noqa: E402
import rag  # noqa: E402

URL = "http://localhost:11434"
CHAT = lp.DEFAULT_MODEL
EMB = "bge-m3"


def post(path, body, timeout=600):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=timeout)


def unload(model):
    try:
        if model == EMB:
            post("/api/embed", {"model": model, "input": ["x"], "keep_alive": 0}).read()
        else:
            post("/api/generate", {"model": model, "keep_alive": 0}).read()
    except Exception:
        pass
    time.sleep(3)


def vram():
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"],
                         capture_output=True, text=True).stdout.strip()
    return out


def runner_ram():
    out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
    rows = [r for r in csv.reader(io.StringIO(out)) if r and r[0].lower().startswith(("llama-server", "ollama"))]
    return "; ".join(f"{r[0]} {int(r[4].replace(',', '').replace(' K', '').replace('K', '').strip() or 0) // 1024} MB"
                     for r in rows)


def stream_chat(messages, max_tokens=350):
    """Return (ttft_ms, total_ms, eval_count, prompt_eval_count, eval_ms, load_ms)."""
    body = {"model": CHAT, "messages": messages, "stream": True, "think": False,
            "options": {"temperature": 0.2, "num_ctx": 4096, "num_predict": max_tokens}}
    t0 = time.perf_counter()
    ttft = None
    last = {}
    with post("/api/chat", body) as r:
        for line in r:
            if not line.strip():
                continue
            d = json.loads(line)
            if ttft is None and (d.get("message") or {}).get("content"):
                ttft = (time.perf_counter() - t0) * 1000
            if d.get("done"):
                last = d
    total = (time.perf_counter() - t0) * 1000
    return (round(ttft or total), round(total), last.get("eval_count"), last.get("prompt_eval_count"),
            round((last.get("eval_duration") or 0) / 1e6), round((last.get("load_duration") or 0) / 1e6))


def main():
    os.environ.update(JALMITRA_RAG="1", JALMITRA_LLM_CACHE="1")
    L = [f"# Performance benchmark ({dt.datetime.now():%Y-%m-%d %H:%M})", "",
         f"Chat model `{CHAT}`, embedding model `{EMB}`, num_ctx 4096, RTX 4050 Laptop 6 GB. "
         "Streaming is used here only to MEASURE time to first token; the app never shows unverified text.", ""]
    # ---- cold loads and memory
    unload(CHAT)
    unload(EMB)
    idle = vram()
    t = time.perf_counter()
    rag.embed_query("warm-up query for the cold load test")
    emb_cold = (time.perf_counter() - t) * 1000
    t = time.perf_counter()
    rag.embed_query("second query, embedding model already loaded")
    emb_warm = (time.perf_counter() - t) * 1000
    ttft0, total0, ev0, pe0, evms0, load0 = stream_chat([{"role": "user", "content": "Say OK."}], 5)
    both = vram()
    ram = runner_ram()
    L += ["## Load and memory", "", "| item | value |", "|---|---|",
          f"| VRAM idle (both models unloaded) | {idle} |", f"| VRAM with chat + embedding model loaded | {both} |",
          f"| Ollama processes RAM (working set) | {ram} |",
          f"| embedding model cold (first query incl. load) | {emb_cold:.0f} ms |",
          f"| embedding query warm | {emb_warm:.0f} ms |",
          f"| chat model cold load (load_duration) | {load0} ms (first request total {total0} ms) |", ""]
    # ---- generation: short / medium / long prompts (built like llm_compose)
    cases = [("short (place answer)", "What is the annual recharge of Phagi?", "data"),
             ("medium (comparison)", "Compare Jaisalmer district with Bikaner district.", "data"),
             ("long (general, 4 passages)", "What is the difference between extraction and recharge? Explain.",
              "general")]
    L += ["## Generation (warm model, 3 runs each, median)", "",
          "| prompt | prompt tokens | time to first token | full generation | output tokens | tokens/s |",
          "|---|---|---|---|---|---|"]
    for label, q, mode in cases:
        out = engine.answer(q, engine.new_state())
        facts = llm_compose.facts_block(out) if mode == "data" else llm_compose.official_definitions()
        passages = rag.retrieve(llm_compose.search_query(q, mode, out), "en", 4)
        passages = [{**p, "text": llm_compose._no_digit_sentences(p["text"])} for p in passages]
        msgs = llm_compose.build_messages(q, "en", facts, passages, mode)
        runs = [stream_chat(msgs) for _ in range(3)]
        med = lambda i: statistics.median(r[i] for r in runs)   # noqa: E731
        tps = statistics.median((r[2] or 0) / (r[4] / 1000) for r in runs if r[4])
        L.append(f"| {label} | {med(3):.0f} | {med(0):.0f} ms | {med(1):.0f} ms | {med(2):.0f} | {tps:.1f} |")
    L.append("")
    # ---- retrieval
    rag.embed_query.__wrapped__ if hasattr(rag.embed_query, "__wrapped__") else None
    rag._embed_cached.cache_clear()
    qs = ["How can groundwater depletion be reduced?", "What does over-exploited mean?",
          "Explain annual groundwater recharge", "Why is the water table deeper before the monsoon?"]
    cold = []
    for q in qs:
        t = time.perf_counter()
        rag.retrieve(q, "en", 4)
        cold.append((time.perf_counter() - t) * 1000)
    cached = []
    for q in qs:
        t = time.perf_counter()
        rag.retrieve(q, "en", 4)
        cached.append((time.perf_counter() - t) * 1000)
    L += ["## RAG retrieval (226 chunks, chromadb, bge-m3)", "", "| case | median | max |", "|---|---|---|",
          f"| new query (embedding + vector search) | {statistics.median(cold):.0f} ms | {max(cold):.0f} ms |",
          f"| repeated query (cached embedding) | {statistics.median(cached):.1f} ms | {max(cached):.1f} ms |", ""]
    # ---- full checked pipeline
    prov = lp.LLMProvider("ollama", model=CHAT, timeout=60)
    llm_compose.clear_cache()
    pq = ["What is the annual recharge of Phagi?", "Is Osian block safe?", "Compare Jaisalmer district with Bikaner district.",
          "What is the difference between extraction and recharge?", "How can groundwater depletion be reduced?",
          "What does Over-Exploited mean?"]
    L += ["## Full checked pipeline (rule answer + retrieval + generation + all checks incl. self-check)", "",
          "| question | rule answer | retrieval | generation | checks (support + self-check) | total AI step | status | "
          "repeat (cached) |", "|---|---|---|---|---|---|---|---|"]
    for q in pq:
        t = time.perf_counter()
        out = engine.answer(q, engine.new_state())
        rule_ms = (time.perf_counter() - t) * 1000
        t = time.perf_counter()
        r1 = llm_compose.enhance(q, out, provider=prov)["llm"]
        first = (time.perf_counter() - t) * 1000
        t = time.perf_counter()
        r2 = llm_compose.enhance(q, out, provider=prov)["llm"]
        again = (time.perf_counter() - t) * 1000
        L.append(f"| {q} | {rule_ms:.1f} ms | {r1.get('retrieval_ms', '-')} ms | {r1.get('llm_ms', '-')} ms | "
                 f"{r1.get('semantic_ms', '-')} ms | {first:.0f} ms | {r1.get('status')} | {again:.1f} ms "
                 f"({r2.get('cache', 'miss')}) |")
    rule_times = []
    for q in pq * 5:
        t = time.perf_counter()
        engine.answer(q, engine.new_state())
        rule_times.append((time.perf_counter() - t) * 1000)
    L += ["", f"Rule-only answers (AI off): median {statistics.median(rule_times):.1f} ms, max {max(rule_times):.1f} ms "
          f"over {len(rule_times)} answers.", "",
          "## What was tried", "",
          "- Streaming: measured above, but NOT used for display. Showing tokens before the checks finish would put "
          "unverified text on screen. Instead the chat shows the verified official answer at once and a "
          "'checking the AI explanation' indicator until the checked text is ready (two-stage answer).",
          "- Caching: verified/rejected outcomes cached in memory (key = question, language, mode, fact block, model, "
          "safety flags; errors never cached); query embeddings cached. Repeated questions take milliseconds.",
          "- Retrieval: 226 chunks, k=4 - vector search itself is a few ms; the query embedding dominates.",
          "- Not done: no bigger or new model, no lower-quality quantisation, no skipped checks."]
    out = HERE / f"perf_v5_{dt.date.today().isoformat()}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
