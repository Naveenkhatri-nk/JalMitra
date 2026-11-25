"""
build_rag_index.py - builds JalMitra's document index for explanations (JalMitra 4.0 Phase 3).

Reads ONLY the three approved PDFs registered in groundwater.db (table data_sources, read-only):
  NC2025  National Compilation on Dynamic Ground Water Resources of India, 2025
  RJ2025  Dynamic Ground Water Resources of Rajasthan - 2025
  AI2025  All India Blockwise GWRA 2025 (categorization of assessment units)

Page-aware chunks (about 500 tokens, ~60-word overlap, never across pages) with metadata
{source_id, title, file, page, chunk_id, year}. Pages that are mostly tables or lists of units are
skipped: figures and categories are answered ONLY from groundwater.db, never from vector search.
Pages whose Devanagari text layer is garbled (broken font mapping in the RJ2025 Hindi pages) are
skipped too.

Output (new folder, nothing else under data/ is written):
  data/rag/chunks.jsonl         every chunk with its metadata
  data/rag/index_report.json    pages read / kept / skipped (with reasons), chunk counts, PDF sha256
  data/rag/chroma/              chromadb collection "jalmitra_docs" (cosine), embeddings from Ollama

Usage:
  python build_rag_index.py --chunks-only        extract + chunk (no embedding model needed)
  python build_rag_index.py                      extract + chunk + embed (needs chromadb + Ollama bge-m3)
Environment: JALMITRA_OLLAMA_URL (default http://localhost:11434), JALMITRA_EMBED_MODEL (default bge-m3)
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "data" / "raw"
DB = BASE / "data" / "groundwater.db"
OUT = BASE / "data" / "rag"
COLLECTION = "jalmitra_docs"
CHUNK_WORDS = 380          # ~500 tokens for English text
OVERLAP_WORDS = 60
MIN_TOKENS = 60

HEADER_LINES = [r"^Dynamic Ground Water Resources of Rajasthan\s*-?\s*2025\s*", r"^National Compilation on Dynamic "
                r"Ground Water Resources of India,?\s*2025\s*", r"^GWRA\s*-\s*2025\s*$"]
MATH_ALNUM = re.compile(r"[\U0001D400-\U0001D7FF]")        # formula glyphs that extract as noise
TABLE_ROW = re.compile(r"^\s*\d{1,4}[.)]?\s+[A-Za-z&]")


def sources():
    """Approved PDFs from data_sources (read-only)."""
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    rows = con.execute("SELECT source_id, file_name, title, assessment_year, sha256 FROM data_sources "
                       "ORDER BY source_id").fetchall()
    con.close()
    return [{"source_id": r[0], "file": r[1], "title": r[2], "year": r[3], "sha256": r[4]} for r in rows]


def page_texts(path):
    """Text of every page. pdfplumber first; pypdfium2 (already installed with pdfplumber) when it sees no pages."""
    import pdfplumber
    with pdfplumber.open(str(path)) as pdf:
        texts = [(p.extract_text() or "") for p in pdf.pages]
    if texts:
        return texts, "pdfplumber"
    import pypdfium2
    doc = pypdfium2.PdfDocument(str(path))
    texts = [doc[i].get_textpage().get_text_range() for i in range(len(doc))]
    return texts, "pypdfium2"


def clean(text):
    lines = []
    for line in text.replace("\r", "").split("\n"):
        line = MATH_ALNUM.sub("", line).strip()
        for h in HEADER_LINES:
            line = re.sub(h, "", line, flags=re.I).strip()
        if line:
            lines.append(line)
    return lines


def skip_reason(lines):
    toks = " ".join(lines).split()
    if len(toks) < MIN_TOKENS:
        return "too little text"
    numeric = sum(1 for t in toks if re.fullmatch(r"[\d.,%()\-/:]+", t)) / len(toks)
    if numeric >= 0.25:
        return "numeric table"
    rows = sum(1 for l in lines if TABLE_ROW.match(l)) / max(1, len(lines))
    if rows >= 0.4:
        return "list of units / table rows"
    joined = " ".join(lines)
    deva = len(re.findall(r"[ऀ-ॿ]", joined))
    latin = len(re.findall(r"[A-Za-z]", joined))
    if deva > latin:
        return "Devanagari text layer (garbled font mapping)"
    if len(re.findall(r"\.{5,}", joined)) >= 5:
        return "table of contents"
    return None


def chunk_page(lines):
    words = " ".join(lines).split()
    out, i = [], 0
    while i < len(words):
        out.append(" ".join(words[i:i + CHUNK_WORDS]))
        if i + CHUNK_WORDS >= len(words):
            break
        i += CHUNK_WORDS - OVERLAP_WORDS
    return out


def build_chunks():
    report = {"documents": [], "chunks": 0}
    chunks = []
    for s in sources():
        path = RAW / s["file"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        texts, reader = page_texts(path)
        kept, skipped = 0, {}
        for pno, text in enumerate(texts, start=1):
            lines = clean(text)
            why = skip_reason(lines)
            if why:
                skipped[why] = skipped.get(why, 0) + 1
                continue
            kept += 1
            for n, body in enumerate(chunk_page(lines)):
                chunks.append({"chunk_id": f"{s['source_id']}-p{pno:03d}-c{n}", "source_id": s["source_id"],
                               "title": s["title"], "file": s["file"], "page": pno, "year": s["year"],
                               "text": body})
        report["documents"].append({**{k: s[k] for k in ("source_id", "title", "file", "year")},
                                    "sha256": digest, "sha256_matches_db": digest == s["sha256"],
                                    "reader": reader, "pages": len(texts), "pages_indexed": kept,
                                    "pages_skipped": skipped,
                                    "chunks": sum(1 for c in chunks if c["source_id"] == s["source_id"])})
    report["chunks"] = len(chunks)
    return chunks, report


def embed(texts, model, url, batch=16):
    import urllib.request
    vecs = []
    for i in range(0, len(texts), batch):
        body = json.dumps({"model": model, "input": texts[i:i + batch]}).encode()
        req = urllib.request.Request(url.rstrip("/") + "/api/embed", data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            vecs.extend(json.loads(r.read())["embeddings"])
        print(f"  embedded {min(i + batch, len(texts))}/{len(texts)}", flush=True)
    return vecs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks-only", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    chunks, report = build_chunks()
    with open(OUT / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    report["built"] = time.strftime("%Y-%m-%d %H:%M:%S")
    report["chunk_words"], report["overlap_words"] = CHUNK_WORDS, OVERLAP_WORDS
    if not a.chunks_only:
        import chromadb
        model = os.environ.get("JALMITRA_EMBED_MODEL", "bge-m3")
        url = os.environ.get("JALMITRA_OLLAMA_URL", "http://localhost:11434")
        t1 = time.time()
        vecs = embed([c["text"] for c in chunks], model, url)
        client = chromadb.PersistentClient(path=str(OUT / "chroma"))
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
        col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine", "embed_model": model})
        col.add(ids=[c["chunk_id"] for c in chunks], embeddings=vecs, documents=[c["text"] for c in chunks],
                metadatas=[{k: c[k] for k in ("source_id", "title", "file", "page", "year")} for c in chunks])
        report["embed_model"], report["embed_dim"] = model, len(vecs[0]) if vecs else None
        report["embed_seconds"] = round(time.time() - t1, 1)
        report["collection_count"] = col.count()
    report["seconds"] = round(time.time() - t0, 1)
    (OUT / "index_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
