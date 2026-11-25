"""
rag.py - retrieval of explanation passages from the three approved reports (JalMitra 4.0 Phase 3).

  retrieve(query, lang="en", k=4) -> [passage, ...]      (empty list when nothing is relevant)

A passage is {"text", "source_id", "title", "file", "page", "chunk_id", "year", "distance"}.
Passages are REFERENCE DATA: lines that look like instructions are removed here, and llm_compose
quotes the rest as data. Figures for places never come from here (they come from groundwater.db).

Needs chromadb and an Ollama embedding model (default bge-m3); the index is built by build_rag_index.py.
Any problem (package missing, index missing, Ollama down, timeout) gives [] and sets last_error.

Environment: JALMITRA_OLLAMA_URL, JALMITRA_EMBED_MODEL (bge-m3), JALMITRA_RAG_MAX_DISTANCE (cosine, 0.55),
JALMITRA_RAG_TIMEOUT (seconds, 15)
"""

import json
import os
import re
import urllib.request
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parent
INDEX = BASE / "data" / "rag" / "chroma"
COLLECTION = "jalmitra_docs"
DEFAULT_MAX_DISTANCE = 0.55   # measured 23 Nov 2026: relevant 0.26-0.55, off-topic 0.56-0.72 (bge-m3, cosine)
MAX_CHARS = 1500

last_error = None
_collection = None

INSTRUCTION_LIKE = re.compile(
    r"ignore\s+(all\s+|the\s+|any\s+|your\s+)?(previous|prior|above|instructions|rules)|disregard|system\s*prompt|"
    r"you\s+are\s+now|act\s+as|pretend|jailbreak|developer\s+mode|new\s+instructions|assistant\s*:|user\s*:|"
    r"<\s*/?\s*(think|script|system|im_start|im_end)|https?://\S+|www\.\S+",
    re.IGNORECASE)


def sanitize(text):
    """Keep the passage as plain reference text: drop instruction-like sentences, links and control characters."""
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text or "")
    parts = re.split(r"(?<=[.!?।])\s+", text)
    kept = [p for p in parts if not INSTRUCTION_LIKE.search(p)]
    out = re.sub(r"\s+", " ", " ".join(kept)).strip()
    return out[:MAX_CHARS]


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def embed_query(text):
    """Query embedding (Phase 5: cached per text / model / server; a failure is not cached)."""
    url = os.environ.get("JALMITRA_OLLAMA_URL", "http://localhost:11434").rstrip("/")
    model = os.environ.get("JALMITRA_EMBED_MODEL", "bge-m3")
    return list(_embed_cached(text, model, url))


@lru_cache(maxsize=512)
def _embed_cached(text, model, url):
    body = json.dumps({"model": model, "input": [text],
                       "keep_alive": os.environ.get("JALMITRA_KEEP_ALIVE", "30m")}).encode()
    req = urllib.request.Request(url + "/api/embed", data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=_env_float("JALMITRA_RAG_TIMEOUT", 15.0)) as r:
        return tuple(json.loads(r.read())["embeddings"][0])


_MANIFEST = None


def manifest():
    """chunk_id -> sha256 of the text, from data/rag/chunks.jsonl written by build_rag_index.py (Phase 5).
    Only chunks listed here, with identical text, may be returned: anything else that got into the vector
    index (tampering, a stale build) is dropped."""
    global _MANIFEST
    if _MANIFEST is None:
        import hashlib
        path = BASE / "data" / "rag" / "chunks.jsonl"
        m = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                c = json.loads(line)
                m[c["chunk_id"]] = hashlib.sha256(c["text"].encode("utf-8")).hexdigest()
        _MANIFEST = m
    return _MANIFEST


def _approved(cid, doc):
    if os.environ.get("JALMITRA_RAG_MANIFEST", "1").strip() in ("0", "false", "off"):   # tests of the cleaning only
        return True
    import hashlib
    return manifest().get(cid) == hashlib.sha256((doc or "").encode("utf-8")).hexdigest()


def _get_collection():
    global _collection
    if _collection is None:
        import chromadb                      # optional dependency (requirements-llm.txt)
        if not INDEX.exists():
            raise FileNotFoundError("RAG index not built (run build_rag_index.py)")
        _collection = chromadb.PersistentClient(path=str(INDEX)).get_collection(COLLECTION)
    return _collection


def retrieve(query, lang="en", k=4, max_distance=None):
    """Up to k relevant passages for the query (any of the six languages; bge-m3 is multilingual)."""
    global last_error
    last_error = None
    limit = max_distance if max_distance is not None else _env_float("JALMITRA_RAG_MAX_DISTANCE",
                                                                     DEFAULT_MAX_DISTANCE)
    try:
        col = _get_collection()
        res = col.query(query_embeddings=[embed_query(query)], n_results=k,
                        include=["documents", "metadatas", "distances"])
    except Exception as e:
        last_error = f"{type(e).__name__}: {e}"[:300]
        return []
    out = []
    try:
        manifest()
    except Exception as e:                          # no manifest -> nothing can be verified -> no passages
        last_error = f"chunk manifest unavailable: {type(e).__name__}"
        return []
    for doc, meta, dist, cid in zip(res["documents"][0], res["metadatas"][0], res["distances"][0], res["ids"][0]):
        if dist is None or dist > limit:
            continue
        if not _approved(cid, doc):
            last_error = f"dropped chunk not in the approved manifest: {cid}"
            continue
        text = sanitize(doc)
        if len(text) < 80:
            continue
        out.append({"text": text, "source_id": meta.get("source_id"), "title": meta.get("title"),
                    "file": meta.get("file"), "page": meta.get("page"), "chunk_id": cid,
                    "year": meta.get("year"), "distance": round(float(dist), 4)})
    return out
